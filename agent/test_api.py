"""
API 测试脚本
验证核心接口功能
"""

import httpx
import asyncio
import json
from datetime import datetime


BASE_URL = "http://localhost:8000"


class APITester:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.access_token = None
        self.refresh_token = None
        self.user_id = None
        self.team_id = None
        
    async def close(self):
        await self.client.aclose()
    
    async def test_health_check(self):
        """测试健康检查"""
        print("\n" + "="*60)
        print("Test 1: Health Check")
        print("="*60)
        
        response = await self.client.get(f"{BASE_URL}/")
        data = response.json()
        
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(data, indent=2)}")
        
        assert response.status_code == 200
        assert data["status"] == "ok"
        print("✅ Health check passed")
    
    async def test_register(self):
        """测试用户注册"""
        print("\n" + "="*60)
        print("Test 2: User Registration")
        print("="*60)
        
        payload = {
            "email": f"test_{datetime.now().timestamp()}@example.com",
            "password": "TestPass@123",
            "name": "Test User"
        }
        
        response = await self.client.post(
            f"{BASE_URL}/api/v1/auth/register",
            json=payload
        )
        data = response.json()
        
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(data, indent=2)}")
        
        assert response.status_code == 200
        assert data["success"] == True
        
        self.test_email = payload["email"]
        self.test_password = payload["password"]
        print("✅ User registration passed")
    
    async def test_login(self):
        """测试用户登录"""
        print("\n" + "="*60)
        print("Test 3: User Login")
        print("="*60)
        
        # 先注册一个用户
        await self.test_register()
        
        payload = {
            "email": self.test_email,
            "password": self.test_password
        }
        
        response = await self.client.post(
            f"{BASE_URL}/api/v1/auth/login",
            json=payload
        )
        data = response.json()
        
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(data, indent=2, default=str)}")
        
        assert response.status_code == 200
        assert "access_token" in data
        assert "refresh_token" in data
        
        self.access_token = data["access_token"]
        self.refresh_token = data["refresh_token"]
        self.user_id = data["user"]["user_id"]
        
        print("✅ User login passed")
    
    async def test_get_current_user(self):
        """测试获取当前用户"""
        print("\n" + "="*60)
        print("Test 4: Get Current User")
        print("="*60)
        
        response = await self.client.get(
            f"{BASE_URL}/api/v1/auth/me",
            headers={"Authorization": f"Bearer {self.access_token}"}
        )
        data = response.json()
        
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(data, indent=2)}")
        
        assert response.status_code == 200
        assert data["success"] == True
        assert data["data"]["email"] == self.test_email
        
        print("✅ Get current user passed")
    
    async def test_create_team(self):
        """测试创建团队"""
        print("\n" + "="*60)
        print("Test 5: Create Team")
        print("="*60)
        
        payload = {
            "name": f"Test Team {datetime.now().timestamp()}",
            "description": "This is a test team for API testing"
        }
        
        response = await self.client.post(
            f"{BASE_URL}/api/v1/teams",
            json=payload,
            headers={"Authorization": f"Bearer {self.access_token}"}
        )
        data = response.json()
        
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(data, indent=2)}")
        
        assert response.status_code == 200
        assert data["success"] == True
        
        self.team_id = data["data"]["team_id"]
        
        print("✅ Create team passed")
    
    async def test_list_teams(self):
        """测试获取团队列表"""
        print("\n" + "="*60)
        print("Test 6: List Teams")
        print("="*60)
        
        response = await self.client.get(
            f"{BASE_URL}/api/v1/teams",
            headers={"Authorization": f"Bearer {self.access_token}"}
        )
        data = response.json()
        
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(data, indent=2)}")
        
        assert response.status_code == 200
        assert data["success"] == True
        
        print("✅ List teams passed")
    
    async def test_invite_member(self):
        """测试邀请成员"""
        print("\n" + "="*60)
        print("Test 7: Invite Team Member")
        print("="*60)
        
        payload = {
            "email": f"invited_{datetime.now().timestamp()}@example.com",
            "role": "editor"
        }
        
        response = await self.client.post(
            f"{BASE_URL}/api/v1/teams/{self.team_id}/invitations",
            json=payload,
            headers={"Authorization": f"Bearer {self.access_token}"}
        )
        data = response.json()
        
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(data, indent=2)}")
        
        assert response.status_code == 200
        assert data["success"] == True
        
        self.invite_code = data["data"]["invite_code"]
        
        print("✅ Invite member passed")
    
    async def run_all_tests(self):
        """运行所有测试"""
        print("\n" + "🚀 "*30)
        print("AgentNex Platform API Test Suite")
        print("🚀 "*30)
        
        try:
            await self.test_health_check()
            await self.test_login()
            await self.test_get_current_user()
            await self.test_create_team()
            await self.test_list_teams()
            await self.test_invite_member()
            
            print("\n" + "✅ "*30)
            print("All tests passed successfully!")
            print("✅ "*30 + "\n")
            
        except AssertionError as e:
            print(f"\n❌ Test failed: {e}")
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await self.close()


async def main():
    tester = APITester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
