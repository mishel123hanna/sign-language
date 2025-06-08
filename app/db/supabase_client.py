# app/services/supabase_client.py
# from supabase import create_client, Client
# from app.core.settings import settings

# # For Supabase-specific features (Storage, Auth, etc.)
# supabase_client: Client = create_client(
#     settings.SUPABASE_PROJECT_URL,  # https://your-project.supabase.co
#     settings.SUPABASE_ANON_KEY
# )

# # Use this for file uploads, auth, etc.
# async def upload_sign_video(file_path: str, file_data: bytes):
#     return supabase_client.storage.from_("sign-videos").upload(file_path, file_data)