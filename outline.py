from outline_vpn.outline_vpn import OutlineVPN

from config import settings

OUTLINE_API_URL = settings.API_URL

client = OutlineVPN(api_url=settings.API_URL,
                    cert_sha256=settings.CERTSHA256)
