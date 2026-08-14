import re
from typing import List, Dict, Any, Optional
from core.logging.logger import logger


class SeatScorer:
    """
    Advanced Seat Scoring Engine.
    Strategy:
      1. Filter by category/section if provided.
      2. Sort rows by proximity (A < B < C, lower numeric rows first).
      3. Within each row, find the first truly contiguous block of `count` seats.
      4. If no contiguous block exists anywhere, fall back to best-available scattered seats.
    """

    @staticmethod
    def _row_sort_key(row_id) -> tuple:
        """
        Normalise a row identifier for sorting so that:
          - numeric rows sort numerically   (1 < 2 < 10)
          - alpha rows sort alphabetically  (A < B < AA)
          - mixed rows (A1, B2 …) sort alpha-then-numeric
          - None / unknown rows go last
        """
        if row_id is None:
            return (999, 0, 0)
        s = str(row_id).strip().upper()
        # Pure numeric
        try:
            return (0, int(s), 0)
        except ValueError:
            pass
        # Pure alpha
        if s.isalpha():
            val = 0
            for ch in s:
                val = val * 26 + (ord(ch) - ord('A') + 1)
            return (1, val, 0)
        # Mixed: split leading alpha from trailing digits
        m = re.match(r'^([A-Z]*)(\d*)$', s)
        if m:
            alpha, num = m.group(1), m.group(2)
            alpha_val = 0
            for ch in alpha:
                alpha_val = alpha_val * 26 + (ord(ch) - ord('A') + 1)
            num_val = int(num) if num else 0
            return (2, alpha_val, num_val)
        return (3, 0, 0)

    @staticmethod
    def _seat_num(seat: dict) -> int:
        """Best-effort seat number extraction."""
        for key in ("seat_number", "seatNumber", "number", "seat_num"):
            v = seat.get(key)
            if v is not None:
                try:
                    return int(v)
                except (ValueError, TypeError):
                    pass
        return 0

    def score_seats(
        self,
        seats_data: List[Dict[str, Any]],
        count: int,
        category: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Return up to `count` seats, preferring a contiguous block in the
        best-quality row within the requested category.
        """
        if not seats_data:
            return []

        # ── 1. Category filter ──────────────────────────────────────────────
        if category and category not in ("Any", "any", ""):
            filtered = [
                s for s in seats_data
                if (
                    s.get("category_name") == category
                    or s.get("category_id") == category
                    or s.get("category_label") == category
                    or s.get("category_key") == category
                )
            ]
            if filtered:
                seats_data = filtered
            else:
                logger.warning(
                    f"[SCORER] No seats matched category='{category}'; "
                    f"searching all {len(seats_data)} seats."
                )

        if not seats_data:
            return []

        # ── 2. Group by row ─────────────────────────────────────────────────
        rows: Dict[str, List[Dict[str, Any]]] = {}
        for seat in seats_data:
            row_id = (
                seat.get("row_id")
                or seat.get("rowId")
                or seat.get("row")
                or "UNKNOWN"
            )
            rows.setdefault(str(row_id), []).append(seat)

        sorted_row_ids = sorted(rows.keys(), key=self._row_sort_key)

        # ── 3. Contiguous block search (best row first) ─────────────────────
        for row_id in sorted_row_ids:
            row_seats = sorted(rows[row_id], key=self._seat_num)
            if len(row_seats) < count:
                continue

            for i in range(len(row_seats) - count + 1):
                block = row_seats[i: i + count]
                nums = [self._seat_num(s) for s in block]
                # Verify strict consecutive integers
                if all(nums[j + 1] == nums[j] + 1 for j in range(len(nums) - 1)):
                    logger.info(
                        f"[SCORER] ✅ Found {count} adjacent seats | "
                        f"row={row_id} seats={nums}"
                    )
                    return block

        # ── 4. Fallback: best-available scattered (sorted by row quality) ───
        all_sorted: List[Dict[str, Any]] = []
        for row_id in sorted_row_ids:
            row_sorted = sorted(rows[row_id], key=self._seat_num)
            all_sorted.extend(row_sorted)

        if len(all_sorted) >= count:
            chosen = all_sorted[:count]
            chosen_nums = [self._seat_num(s) for s in chosen]
            logger.warning(
                f"[SCORER] ⚠️ No adjacent block found; "
                f"returning {count} scattered seats: {chosen_nums}"
            )
            return chosen

        logger.warning(
            f"[SCORER] ❌ Not enough seats: need={count} available={len(all_sorted)}"
        )
        return all_sorted
