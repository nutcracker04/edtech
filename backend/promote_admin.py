import sys
import os
import asyncio
from supabase import create_client, Client

# Add the current directory to sys.path to allow importing app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.config import settings

def promote_to_admin(email: str):
    print(f"Connecting to Supabase at {settings.supabase_url}...")
    try:
        supabase: Client = create_client(settings.supabase_url, settings.supabase_service_key)
    except Exception as e:
        print(f"Failed to initialize Supabase client: {e}")
        return

    print(f"Looking up user with email: {email}")
    
    # Find user by email
    # Note: list_users is the most reliable way without having the ID
    user_id = None
    
    try:
        # Paginating to find the user
        # Note: gotrue-py (underlying auth lib) implementation of list_users
        users_response = supabase.auth.admin.list_users(page=1, per_page=1000)
        # users_response is usually a UserList object or similar
        
        for user in users_response:
             if user.email == email:
                user_id = user.id
                break
                
        if not user_id:
            print(f"Error: User with email {email} not found.")
            print("Please ensure you have signed up first.")
            return

        print(f"Found user {email} with ID: {user_id}")
        
        # Update the user's role to 'admin'
        # This updates the 'role' column in auth.users schema (for JWT/Backend)
        print("Promoting user to admin (auth.users)...")
        response = supabase.auth.admin.update_user_by_id(
            user_id, 
            {"role": "admin"}
        )
        
        # Also update the public.users table (for Frontend profile)
        print("Updating public profile (public.users)...")
        try:
            # We use the service key, so we assume we have RLS bypass or policy to update
            rpc_response = supabase.table("users").update({"role": "admin"}).eq("id", user_id).execute()
            if not rpc_response.data:
                print("Warning: Could not update public.users table. Does the record exist?")
            else:
                print("Successfully updated public profile.")
        except Exception as e:
            print(f"Error updating public profile: {e}")
        
        print(f"Successfully promoted {email} to admin!")
        print("The user needs to sign out and sign directly back in for the new role to take effect in their token.")
        
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python promote_admin.py <email>")
        print("Example: python promote_admin.py user@example.com")
        sys.exit(1)
        
    email = sys.argv[1]
    promote_to_admin(email)
