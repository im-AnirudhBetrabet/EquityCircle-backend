from fastapi import APIRouter, HTTPException, Depends
from typing import List
from app.core.security import get_current_user, verify_group_membership
from app.db.supabase import supabase
from app.schemas.cohort import CohortRead, CohortCreate

router = APIRouter()

@router.get("/", response_model=List[CohortRead])
def get_active_cohorts(group_id: str, current_user = Depends(get_current_user)):
    """
    Fetches all the OPEN cohorts for a specified group
    """
    try:
        verify_group_membership(current_user.id, group_id)
        response = supabase.table("cohorts").select("*").eq("group_id", group_id).eq("status", "OPEN").execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=CohortRead)
def create_cohort(cohort: CohortCreate, current_user = Depends(get_current_user)):
    """
    Open a new monthly cohort (e.g., APR_2026)
    """
    try:
        verify_group_membership(current_user.id, str(cohort.group_id))
        data_to_insert = cohort.model_dump(mode='json')
        response       = supabase.table("cohorts").insert(data_to_insert).execute()

        if not response.data:
            raise HTTPException(status_code=400, detail="Failed to create cohort")

        return response.data[0]
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))