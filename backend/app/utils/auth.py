import requests
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from app.config import settings
import base64
import json

security = HTTPBearer()

# Cache for JWKS
_jwks_cache = None

def get_jwks():
    global _jwks_cache
    if _jwks_cache:
        return _jwks_cache
    
    try:
        url = f"{settings.supabase_url}/auth/v1/.well-known/jwks.json"
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            _jwks_cache = resp.json()
            return _jwks_cache
    except Exception as e:
        print(f"Failed to fetch JWKS: {e}")
    return None

def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)) -> dict:
    """
    Verify JWT token from Supabase Auth.
    Supports both HS256 (Secret) and ES256 (JWKS).
    Returns the decoded token payload with user information.
    """
    token = credentials.credentials
    
    try:
        # 1. Inspect unverified header to determine algorithm
        unverified_header = jwt.get_unverified_header(token)
        alg = unverified_header.get("alg")
        
        payload = None

        if alg == "HS256":
            # Verify with Secret
            try:
                payload = jwt.decode(
                    token,
                    settings.supabase_jwt_secret,
                    algorithms=["HS256"],
                    audience="authenticated"
                )
            except JWTError:
                # Fallback: Try decoding base64 secret
                try:
                    decoded_secret = base64.b64decode(settings.supabase_jwt_secret)
                    payload = jwt.decode(
                        token,
                        decoded_secret,
                        algorithms=["HS256"],
                        audience="authenticated"
                    )
                except Exception:
                    raise JWTError("Signature verification failed with HS256")
                    
        elif alg == "ES256" or alg == "RS256":
            # Verify with JWKS
            jwks = get_jwks()
            if not jwks:
                raise HTTPException(status_code=500, detail="Could not fetch JWKS for key verification")
            
            # python-jose can verify against JWKS directly? No, it needs the key constructed.
            # We can pass the JWK dict or keys list to some libs, but python-jose signature verify 
            # might need us to find the specific key.
            
            # Find the key
            kid = unverified_header.get("kid")
            key = next((k for k in jwks["keys"] if k["kid"] == kid), None)
            
            if not key:
                # Refresh cache once and try again
                global _jwks_cache
                _jwks_cache = None
                jwks = get_jwks()
                key = next((k for k in jwks["keys"] if k["kid"] == kid), None)
            
            if not key:
                raise JWTError(f"Public key not found for kid: {kid}")
                
            payload = jwt.decode(
                token,
                key, # python-jose handles JWK dict as key
                algorithms=[alg],
                audience="authenticated"
            )
            
        else:
            raise JWTError(f"Unsupported algorithm: {alg}")
        
        # Extract user_id
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials: No sub claim",
            )
        
        return {
            "user_id": user_id,
            "email": payload.get("email"),
            "role": payload.get("role"),
            "token": token
        }
    
    except JWTError as e:
        print(f"JWT Verification Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication credentials: {str(e)}",
        )



def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)) -> dict:
    """
    Dependency to get current authenticated user.
    Use this in routes that require authentication.
    """
    return verify_token(credentials)
