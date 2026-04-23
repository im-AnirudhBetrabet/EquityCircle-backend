from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from app.db.supabase import supabase
from app.core.security import get_current_user, verify_group_membership
from app.schemas.group import GroupCreate, GroupRead, GroupRequestRead, RequestUpdate
from app.services.logger import sys_logger
router = APIRouter()

@router.get("/", response_model=Optional[List[GroupRead]])
def get_user_groups(current_user = Depends(get_current_user)):
    """
    Retrieve the groups where the user is a member.
    """
    try:
        current_user_id = current_user.id
        response        = supabase.table("group_members").select("role, joined_at, groups(*)").eq("user_id", current_user_id).execute()

        formatted_groups = []
        for membership in response.data:
            group_data = membership.get("groups")
            if group_data:  # Ensure the group actually exists
                # Attach the user's specific role and join date to the group object
                group_data["user_role"] = membership.get("role")
                group_data["joined_at"] = membership.get("joined_at")
                formatted_groups.append(group_data)

        return formatted_groups

    except Exception as e:
        sys_logger.error(e)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=Optional[GroupRead])
def create_group(group: GroupCreate, current_user=Depends(get_current_user)):
    """ Create a new group and assign the creator as the ADMIN. """
    try:
        group_res = supabase.table("groups").insert({"name": group.name}).execute()
        new_group = group_res.data[0]
        supabase.table("group_members").insert({
            "group_id": new_group["id"],
            "user_id" : current_user.id,
            "role"    : "admin"
        }).execute()
        return new_group
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search", response_model=Optional[List[GroupRead]])
def search_group(query: str = "", current_user=Depends(get_current_user)):
    try:
        res = supabase.table("groups").select("*").ilike("name", f"%{query}%").limit(20).execute()
        return res.data
    except Exception as e:
        sys_logger.error(e)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{group_id}/join-request",response_model=Optional[GroupRequestRead])
def request_to_join(group_id: str, current_user=Depends(get_current_user)):
    try:
        existing = supabase.table("group_requests").select("*").eq("user_id", current_user.id).eq("group_id",group_id).eq("status", "PENDING").execute()
        if existing.data:
            raise HTTPException(status_code=400, detail="You already have a pending request")
        res = supabase.table("group_requests").insert({
            "group_id": group_id,
            "user_id" : current_user.id,
            "status"  : "PENDING"
        }).execute()
        return res.data[0]
    except Exception as e:
        if isinstance(e, HTTPException):
            sys_logger.error(e)
            raise e
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{group_id}/join-requests", response_model=Optional[List[GroupRequestRead]])
def get_pending_requests(group_id: str, current_user=Depends(get_current_user)):
    try:
        verify_group_membership(current_user.id, group_id, require_admin=True)
        res = supabase.table("group_requests").select("*, profiles(display_name)").eq("group_id", group_id).eq("status","PENDING").execute()
        if res.data:
            return res.data
        return []
    except Exception as e:
        if isinstance(e, HTTPException):
            sys_logger.error(e)
            raise e
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/requests/{request_id}")
def handle_join_request(request_id: str, update: RequestUpdate, current_user=Depends(get_current_user)):
    """ Admin only: Approve or reject a pending request. """
    try:
        req_res = supabase.table("group_requests").select("*").eq("id", request_id).execute()
        if not req_res.data:
            sys_logger.error(f"Request not found: {request_id}")
            raise HTTPException(status_code=404, detail="Request not found")

        request_data = req_res.data[0]
        target_group_id = request_data["group_id"]
        target_user_id = request_data["user_id"]
        verify_group_membership(current_user.id, target_group_id, require_admin=True)
        supabase.table("group_requests").update({"status": update.status}).eq("id", request_id).execute()
        if update.status == "APPROVED":
            supabase.table("group_members").insert({
                "group_id": target_group_id,
                "user_id" : target_user_id,
                "role"    : "member"
            }).execute()
        return {"message": f"Request {update.status.lower()} successfully"}
    except Exception as e:
        sys_logger.error(e)
        raise HTTPException(status_code=500, detail=str(e))
