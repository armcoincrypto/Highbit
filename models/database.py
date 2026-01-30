"""
SQLite database for transfer requests.
"""
import asyncio
import json
import logging
import os
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Optional, List

from config import DATABASE_PATH

log = logging.getLogger(__name__)


class RequestStatus(Enum):
    """Transfer request status."""
    NEW = "new"
    ASSIGNED = "assigned"
    CONTACTED = "contacted"
    PAYMENT_RECEIVED = "payment_received"
    SENT = "sent"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass
class TransferRequest:
    """Transfer request record."""
    id: int
    user_id: int
    username: Optional[str]
    created_at: datetime
    cny_amount: Decimal
    usd_equiv: Decimal
    method: str  # alipay/wechat/bank
    pay_currency: str  # AMD/USD/RUB/USDT
    amount_due: Decimal
    discount_pct: Decimal
    htx_price: Decimal
    cba_rates_json: str
    status: RequestStatus
    assigned_admin_id: Optional[int]
    notes: Optional[str]
    scheduled_time: Optional[str]
    updated_at: datetime

    @classmethod
    def from_row(cls, row: tuple) -> "TransferRequest":
        return cls(
            id=row[0],
            user_id=row[1],
            username=row[2],
            created_at=datetime.fromisoformat(row[3]),
            cny_amount=Decimal(row[4]),
            usd_equiv=Decimal(row[5]),
            method=row[6],
            pay_currency=row[7],
            amount_due=Decimal(row[8]),
            discount_pct=Decimal(row[9]),
            htx_price=Decimal(row[10]),
            cba_rates_json=row[11],
            status=RequestStatus(row[12]),
            assigned_admin_id=row[13],
            notes=row[14],
            scheduled_time=row[15],
            updated_at=datetime.fromisoformat(row[16]) if row[16] else datetime.now(),
        )


@dataclass
class RequestFile:
    """File attached to a request (QR codes, bank details, etc.)."""
    id: int
    request_id: int
    file_id: str  # Telegram file_id
    file_type: str  # photo/document
    created_at: datetime


@dataclass
class StatusChange:
    """Status change history."""
    id: int
    request_id: int
    old_status: str
    new_status: str
    admin_id: Optional[int]
    changed_at: datetime
    note: Optional[str]


class Database:
    """SQLite database wrapper with async support."""

    _instance: Optional["Database"] = None
    _lock = asyncio.Lock()

    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path
        self._ensure_directory()
        self._init_db()

    @classmethod
    async def get_instance(cls) -> "Database":
        async with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def _ensure_directory(self):
        """Ensure database directory exists."""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def _get_conn(self):
        """Get database connection with proper cleanup."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_db(self):
        """Initialize database schema."""
        with self._get_conn() as conn:
            cur = conn.cursor()

            # Requests table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    username TEXT,
                    created_at TEXT NOT NULL DEFAULT (datetime('now')),
                    cny_amount TEXT NOT NULL,
                    usd_equiv TEXT NOT NULL,
                    method TEXT NOT NULL,
                    pay_currency TEXT NOT NULL,
                    amount_due TEXT NOT NULL,
                    discount_pct TEXT NOT NULL,
                    htx_price TEXT NOT NULL,
                    cba_rates_json TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'new',
                    assigned_admin_id INTEGER,
                    notes TEXT,
                    scheduled_time TEXT,
                    updated_at TEXT DEFAULT (datetime('now'))
                )
            """)

            # Request files table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS request_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    request_id INTEGER NOT NULL,
                    file_id TEXT NOT NULL,
                    file_type TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT (datetime('now')),
                    FOREIGN KEY (request_id) REFERENCES requests(id)
                )
            """)

            # Status history table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS status_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    request_id INTEGER NOT NULL,
                    old_status TEXT NOT NULL,
                    new_status TEXT NOT NULL,
                    admin_id INTEGER,
                    changed_at TEXT NOT NULL DEFAULT (datetime('now')),
                    note TEXT,
                    FOREIGN KEY (request_id) REFERENCES requests(id)
                )
            """)

            # Indexes
            cur.execute("CREATE INDEX IF NOT EXISTS idx_requests_user_id ON requests(user_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_requests_status ON requests(status)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_request_files_request_id ON request_files(request_id)")

            log.info("Database initialized at %s", self.db_path)

    # =========================================================================
    # Request CRUD
    # =========================================================================

    def create_request(
        self,
        user_id: int,
        username: Optional[str],
        cny_amount: Decimal,
        usd_equiv: Decimal,
        method: str,
        pay_currency: str,
        amount_due: Decimal,
        discount_pct: Decimal,
        htx_price: Decimal,
        cba_rates: dict,
        scheduled_time: Optional[str] = None,
    ) -> int:
        """Create a new transfer request. Returns request ID."""
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO requests (
                    user_id, username, cny_amount, usd_equiv, method, pay_currency,
                    amount_due, discount_pct, htx_price, cba_rates_json, scheduled_time
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    username,
                    str(cny_amount),
                    str(usd_equiv),
                    method,
                    pay_currency,
                    str(amount_due),
                    str(discount_pct),
                    str(htx_price),
                    json.dumps(cba_rates),
                    scheduled_time,
                )
            )
            request_id = cur.lastrowid
            log.info("Created request #%d for user %d: %s CNY", request_id, user_id, cny_amount)
            return request_id

    def get_request(self, request_id: int) -> Optional[TransferRequest]:
        """Get a request by ID."""
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM requests WHERE id = ?",
                (request_id,)
            )
            row = cur.fetchone()
            if row:
                return TransferRequest.from_row(tuple(row))
            return None

    def get_user_requests(self, user_id: int, limit: int = 10) -> List[TransferRequest]:
        """Get recent requests for a user."""
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM requests WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
                (user_id, limit)
            )
            return [TransferRequest.from_row(tuple(row)) for row in cur.fetchall()]

    def get_requests_by_status(self, status: RequestStatus, limit: int = 50) -> List[TransferRequest]:
        """Get requests by status."""
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM requests WHERE status = ? ORDER BY created_at DESC LIMIT ?",
                (status.value, limit)
            )
            return [TransferRequest.from_row(tuple(row)) for row in cur.fetchall()]

    def get_active_requests(self, limit: int = 50) -> List[TransferRequest]:
        """Get all active (non-completed, non-cancelled) requests."""
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT * FROM requests
                WHERE status NOT IN ('completed', 'cancelled')
                ORDER BY created_at DESC LIMIT ?
                """,
                (limit,)
            )
            return [TransferRequest.from_row(tuple(row)) for row in cur.fetchall()]

    def update_request_status(
        self,
        request_id: int,
        new_status: RequestStatus,
        admin_id: Optional[int] = None,
        note: Optional[str] = None,
    ) -> bool:
        """Update request status and record history."""
        with self._get_conn() as conn:
            cur = conn.cursor()

            # Get current status
            cur.execute("SELECT status FROM requests WHERE id = ?", (request_id,))
            row = cur.fetchone()
            if not row:
                return False

            old_status = row[0]

            # Update status
            cur.execute(
                """
                UPDATE requests SET status = ?, updated_at = datetime('now'),
                assigned_admin_id = COALESCE(?, assigned_admin_id)
                WHERE id = ?
                """,
                (new_status.value, admin_id, request_id)
            )

            # Record history
            cur.execute(
                """
                INSERT INTO status_history (request_id, old_status, new_status, admin_id, note)
                VALUES (?, ?, ?, ?, ?)
                """,
                (request_id, old_status, new_status.value, admin_id, note)
            )

            log.info("Request #%d: %s -> %s (admin: %s)", request_id, old_status, new_status.value, admin_id)
            return True

    def add_note(self, request_id: int, note: str) -> bool:
        """Add/update note on request."""
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE requests SET notes = COALESCE(notes || '\n', '') || ? WHERE id = ?",
                (note, request_id)
            )
            return cur.rowcount > 0

    # =========================================================================
    # Files
    # =========================================================================

    def add_file(self, request_id: int, file_id: str, file_type: str) -> int:
        """Add a file to a request."""
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO request_files (request_id, file_id, file_type) VALUES (?, ?, ?)",
                (request_id, file_id, file_type)
            )
            return cur.lastrowid

    def get_request_files(self, request_id: int) -> List[RequestFile]:
        """Get all files for a request."""
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM request_files WHERE request_id = ?",
                (request_id,)
            )
            return [
                RequestFile(
                    id=row[0],
                    request_id=row[1],
                    file_id=row[2],
                    file_type=row[3],
                    created_at=datetime.fromisoformat(row[4]),
                )
                for row in cur.fetchall()
            ]

    # =========================================================================
    # Status History
    # =========================================================================

    def get_status_history(self, request_id: int) -> List[StatusChange]:
        """Get status change history for a request."""
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM status_history WHERE request_id = ? ORDER BY changed_at",
                (request_id,)
            )
            return [
                StatusChange(
                    id=row[0],
                    request_id=row[1],
                    old_status=row[2],
                    new_status=row[3],
                    admin_id=row[4],
                    changed_at=datetime.fromisoformat(row[5]),
                    note=row[6],
                )
                for row in cur.fetchall()
            ]

    # =========================================================================
    # Statistics
    # =========================================================================

    def get_stats(self) -> dict:
        """Get basic statistics."""
        with self._get_conn() as conn:
            cur = conn.cursor()

            cur.execute("SELECT COUNT(*) FROM requests")
            total = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM requests WHERE status = 'completed'")
            completed = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM requests WHERE status NOT IN ('completed', 'cancelled')")
            active = cur.fetchone()[0]

            cur.execute("SELECT SUM(CAST(cny_amount AS REAL)) FROM requests WHERE status = 'completed'")
            total_cny = cur.fetchone()[0] or 0

            return {
                "total_requests": total,
                "completed": completed,
                "active": active,
                "total_cny_volume": total_cny,
            }


async def get_database() -> Database:
    """Get singleton database instance."""
    return await Database.get_instance()
