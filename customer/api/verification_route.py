# from fastapi import APIRouter, File, UploadFile, Depends, HTTPException, BackgroundTasks
# from typing import Dict, Optional
# from dependency_injector.wiring import inject, Provide
# import uuid

# from bootstrap.container import Container
# from Customer.services.verification_service import VerificationService, VerificationResult
# from Customer.dto.requests.customer_request import CustomerCreateRequest
# from persistence.db.models.customer import Customer

# router = APIRouter(
#     prefix="/verify",
#     tags=["Customer Verification"]
# )

# # Store verification sessions in memory (in production, use Redis/DB)
# verification_sessions = {}

# @router.post("/document")
# @inject
# async def verify_document(
#     document: UploadFile = File(...),
#     verification_service: VerificationService = Depends(Provide[Container.verification_service])
# ) -> Dict:
#     """
#     Step 1: Verify uploaded ID document and extract information
#     Returns a session token for subsequent steps
#     """
#     try:
#         # Read document image
#         contents = await document.read()

#         # Process document and extract info
#         result = await verification_service.verify_document(contents)

#         if not result.success:
#             raise HTTPException(status_code=400, detail=result.message)

#         # Create a new verification session
#         session_id = str(uuid.uuid4())
#         verification_sessions[session_id] = {
#             "document_info": result.details,
#             "document_image_path": result.details.get("image_path"),  # S3 path
#             "status": "document_verified"
#         }

#         return {
#             "session_id": session_id,
#             "message": "Document verified successfully",
#             "extracted_info": result.details.get("extracted_info")
#         }

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# @router.post("/selfie/{session_id}")
# @inject
# async def verify_selfie(
#     session_id: str,
#     selfie: UploadFile = File(...),
#     verification_service: VerificationService = Depends(Provide[Container.verification_service])
# ) -> Dict:
#     """
#     Step 2: Process selfie image
#     - Compare with ID photo
#     """
#     if session_id not in verification_sessions:
#         raise HTTPException(status_code=404, detail="Invalid or expired session")

#     session = verification_sessions[session_id]
#     if session["status"] != "document_verified":
#         raise HTTPException(status_code=400, detail="Document verification required first")

#     try:
#         contents = await selfie.read()

#         # Compare faces
#         result = await verification_service.verify_biometrics(
#             selfie_image=contents,
#             id_photo_path=session["document_image_path"]
#         )

#         if not result.success:
#             raise HTTPException(status_code=400, detail=result.message)

#         # Update session
#         session["status"] = "biometrics_verified"
#         session["selfie_path"] = result.details.get("selfie_path")  # S3 path

#         return {
#             "message": "Face verification successful",
#             "details": {
#                 "face_match_score": result.details.get("face_match_score")
#             }
#         }

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# @router.post("/register/{session_id}")
# @inject
# async def register_customer(
#     session_id: str,
#     customer_data: CustomerCreateRequest,
#     verification_service: VerificationService = Depends(Provide[Container.verification_service]),
#     background_tasks: BackgroundTasks
# ) -> Dict:
#     """
#     Step 3: Complete registration
#     - Verify all steps are completed
#     - Create customer record
#     """
#     if session_id not in verification_sessions:
#         raise HTTPException(status_code=404, detail="Invalid or expired session")

#     session = verification_sessions[session_id]
#     if session["status"] != "biometrics_verified":
#         raise HTTPException(status_code=400, detail="Complete document and face verification first")

#     try:
#         # Create customer record with verified information
#         result = await verification_service.complete_verification(
#             session=session,
#             customer_data=customer_data
#         )

#         if not result.success:
#             raise HTTPException(status_code=400, detail=result.message)

#         # Clean up session in background
#         background_tasks.add_task(verification_sessions.pop, session_id, None)

#         return {
#             "message": "Registration completed successfully",
#             "customer_id": result.details.get("customer_id")
#         }

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# @router.get("/session/{session_id}")
# async def get_verification_status(session_id: str) -> Dict:
#     """Get current verification session status"""
#     if session_id not in verification_sessions:
#         raise HTTPException(status_code=404, detail="Invalid or expired session")

#     session = verification_sessions[session_id]
#     return {
#         "status": session["status"],
#         "document_info": session.get("document_info"),
#         "has_selfie": "selfie_path" in session
#     }
