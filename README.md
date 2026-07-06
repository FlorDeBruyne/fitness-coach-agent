# Creating a invitiation token for the Apple app

1. Create a bearer token:
curl -X POST http://api.ai-fitness-coach.be/api/v1/auth/login   -H "Content-Type: application/x-www-form-urlencoded"   -d "username={USERNAME}&password={PASSWORD}"

2. Create an invitation code:
curl -X POST http://api.ai-fitness-coach.be/api/v1/users/{USER_ID}/invitation-code   -H "Authorization: Bearer {BEARER_TOKEN}"