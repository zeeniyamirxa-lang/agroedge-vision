"""
database.py — AgroEdge-Vision cloud database module using Supabase.
"""
import streamlit as st
import uuid
from supabase import create_client, Client

SUPABASE_URL = "https://chwkhuvjivyozisckocx.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNod2todXZqaXZ5b3ppc2Nrb2N4Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3OTE5NzIyNywiZXhwIjoyMDk0NzczMjI3fQ.9vQ3PO5OQKo5ydHEiZG4hMpSK93FzhP--KyH2BJW1X0"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

_LS_KEY = "agroedge_guest_id"
_QP_KEY = "uid"


def _init():
    """Establish a stable guest_user_id that survives page refreshes.

    Strategy (three-layer persistence):
      1. st.session_state  — survives reruns within one browser tab session.
      2. st.query_params   — survives hard refresh because the UUID lives in
                             the URL (?uid=...) and Streamlit re-reads it on
                             every cold boot.
      3. localStorage (JS) — repopulates the query param on future visits even
                             if the user navigates to the bare URL.

    Priority order on read: session_state → query_params → generate new.
    On first generation the UUID is written to both query_params and localStorage.
    """
    # 1. Already set this run — nothing to do.
    if "guest_user_id" in st.session_state:
        return

    # 2. Try to recover from the URL query param (?uid=...).
    uid_from_qp = st.query_params.get(_QP_KEY, "")
    if uid_from_qp:
        try:
            # Validate it's actually a UUID before trusting it.
            validated = str(uuid.UUID(uid_from_qp))
            st.session_state["guest_user_id"] = validated
            # Keep query param in sync (no-op if already correct).
            st.query_params[_QP_KEY] = validated
            # Re-arm localStorage so it stays warm for next bare-URL visit.
            _inject_localstorage_writer(validated)
            return
        except ValueError:
            pass  # Tampered/invalid param — fall through to generate new.

    # 3. No valid param found — generate a fresh UUID, persist everywhere.
    new_uid = str(uuid.uuid4())
    st.session_state["guest_user_id"] = new_uid
    st.query_params[_QP_KEY] = new_uid
    _inject_localstorage_writer(new_uid)


def _inject_localstorage_writer(uid: str):
    """Inject a tiny JS snippet that writes the UUID to localStorage AND
    redirects bare-URL visits to include ?uid=... so the query-param layer
    is always populated even after copy-pasting the root URL.
    """
    st.html(f"""
    <script>
    (function() {{
      var KEY = "{_LS_KEY}";
      var UID = "{uid}";
      // Always keep localStorage warm.
      try {{ localStorage.setItem(KEY, UID); }} catch(e) {{}}

      // If the URL has no ?uid param, redirect to add it so Python sees it
      // on the very next Streamlit rerun (covers copy-paste / bare-URL visits).
      var params = new URLSearchParams(window.location.search);
      if (!params.get("uid")) {{
        params.set("uid", UID);
        var newUrl = window.location.pathname + "?" + params.toString();
        window.history.replaceState(null, "", newUrl);
      }}
    }})();
    </script>
    """)


def _get_current_user() -> str:
    """Return the canonical UUID string for the current session.
    Always calls _init() first — never generates a one-off UUID.
    """
    _init()
    return str(uuid.UUID(st.session_state["guest_user_id"]))


def add_log(disease_name: str, confidence: float):
    """Insert a scan result into the cloud table tagged with the session UUID."""
    try:
        current_user = _get_current_user()
        payload = {
            "disease_name": str(disease_name),
            "confidence": float(confidence),
            "status": "healthy" if "healthy" in str(disease_name).lower() else "unhealthy",
            "user_id": current_user,
        }
        response = supabase.table("plant_history").insert(payload).execute()
        return response
    except Exception as e:
        print(f"[-] Insert failed: {e}")
        return None


def get_all_logs():
    """Fetch only this session's scan history from Supabase, newest first."""
    try:
        current_user = _get_current_user()
        # Use PostgREST filter directly via params to avoid supabase-py .eq() bug
        response = (
            supabase.table("plant_history")
            .select("*")
            .order("created_at", desc=True)
            .execute()
        )
        all_rows = response.data if response.data else []
        # Filter in Python — guaranteed to work regardless of supabase-py version
        return [r for r in all_rows if r.get("user_id") == current_user]
    except Exception as e:
        print(f"[-] Fetch failed: {e}")
        return []


def delete_log(record_id: int) -> bool:
    """Delete a scan row by its integer ID using raw filter to avoid supabase-py .eq() bug."""
    try:
        # .eq() is broken in this version of supabase-py for integer columns (PGRST100).
        # Use the PostgREST filter string directly instead.
        supabase.table("plant_history").delete().filter("id", "eq", record_id).execute()
        return True
    except Exception as e:
        print(f"[-] Delete failed: {e}")
        return False


def get_total_scans() -> int:
    return len(get_all_logs())