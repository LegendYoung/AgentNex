"""
P0 阶段完整验证脚本
验证所有核心功能是否正常工作
"""

import httpx
import asyncio
import json
import sys
from datetime import datetime
from typing import Dict, Any


class P0Validator:
    """P0 阶段验证器"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
        self.access_token = None
        self.refresh_token = None
        self.user_id = None
        self.team_id = None
        self.agent_id = None
        self.kb_id = None
        self.test_results = []
    
    async def close(self):
        await self.client.aclose()
    
    def log_test(self, test_name: str, passed: bool, details: str = ""):
        """记录测试结果"""
        result = {
            "test": test_name,
            "passed": passed,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
        if details:
            print(f"    {details}")
    
    async def test_health_check(self) -> bool:
        """测试健康检查"""
        try:
            response = await self.client.get(f"{self.base_url}/")
            data = response.json()
            
            passed = (
                response.status_code == 200 and
                data.get("status") == "ok" and
                "features" in data
            )
            
            self.log_test(
                "Health Check",
                passed,
                f"Status: {data.get('status')}, Features: {len(data.get('features', []))}"
            )
            
            return passed
        except Exception as e:
            self.log_test("Health Check", False, str(e))
            return False
    
    async def test_user_registration(self) -> bool:
        """测试用户注册"""
        try:
            payload = {
                "email": f"p0_test_{datetime.now().timestamp()}@example.com",
                "password": "TestPass@123",
                "name": "P0 Test User"
            }
            
            response = await self.client.post(
                f"{self.base_url}/api/v1/auth/register",
                json=payload
            )
            
            passed = response.status_code == 200
            
            if passed:
                self.test_email = payload["email"]
                self.test_password = payload["password"]
            
            self.log_test("User Registration", passed)
            return passed
        except Exception as e:
            self.log_test("User Registration", False, str(e))
            return False
    
    async def test_user_login(self) -> bool:
        """测试用户登录"""
        try:
            payload = {
                "email": self.test_email,
                "password": self.test_password
            }
            
            response = await self.client.post(
                f"{self.base_url}/api/v1/auth/login",
                json=payload
            )
            
            data = response.json()
            
            passed = (
                response.status_code == 200 and
                "access_token" in data and
                "refresh_token" in data
            )
            
            if passed:
                self.access_token = data["access_token"]
                self.refresh_token = data["refresh_token"]
                self.user_id = data["user"]["user_id"]
            
            self.log_test("User Login", passed)
            return passed
        except Exception as e:
            self.log_test("User Login", False, str(e))
            return False
    
    async def test_token_auth(self) -> bool:
        """测试 Token 鉴权"""
        try:
            # 有 Token 的请求
            response_valid = await self.client.get(
                f"{self.base_url}/api/v1/auth/me",
                headers={"Authorization": f"Bearer {self.access_token}"}
            )
            
            # 无 Token 的请求
            response_invalid = await self.client.get(
                f"{self.base_url}/api/v1/users"
            )
            
            passed = (
                response_valid.status_code == 200 and
                response_invalid.status_code == 401
            )
            
            self.log_test("Token Authentication", passed)
            return passed
        except Exception as e:
            self.log_test("Token Authentication", False, str(e))
            return False
    
    async def test_team_creation(self) -> bool:
        """测试团队创建"""
        try:
            payload = {
                "name": f"P0 Test Team {datetime.now().timestamp()}",
                "description": "Test team for P0 validation"
            }
            
            response = await self.client.post(
                f"{self.base_url}/api/v1/teams",
                json=payload,
                headers={"Authorization": f"Bearer {self.access_token}"}
            )
            
            data = response.json()
            
            passed = (
                response.status_code == 200 and
                data.get("success") == True
            )
            
            if passed:
                self.team_id = data["data"]["team_id"]
            
            self.log_test("Team Creation", passed)
            return passed
        except Exception as e:
            self.log_test("Team Creation", False, str(e))
            return False
    
    async def test_team_invitation(self) -> bool:
        """测试团队邀请"""
        try:
            payload = {
                "email": f"invited_{datetime.now().timestamp()}@example.com",
                "role": "editor"
            }
            
            response = await self.client.post(
                f"{self.base_url}/api/v1/teams/{self.team_id}/invitations",
                json=payload,
                headers={"Authorization": f"Bearer {self.access_token}"}
            )
            
            data = response.json()
            
            passed = (
                response.status_code == 200 and
                data.get("success") == True and
                "invite_code" in data["data"]
            )
            
            self.log_test("Team Invitation", passed)
            return passed
        except Exception as e:
            self.log_test("Team Invitation", False, str(e))
            return False
    
    async def test_agent_creation(self) -> bool:
        """测试 Agent 创建"""
        try:
            payload = {
                "name": f"P0 Test Agent {datetime.now().timestamp()}",
                "description": "Test agent for P0 validation",
                "system_prompt": "You are a helpful test assistant.",
                "model_id": "qwen-plus",
                "temperature": 70,
                "top_p": 90,
                "enable_memory": False,
                "enable_knowledge": False,
                "enable_tools": False,
                "is_public": False
            }
            
            response = await self.client.post(
                f"{self.base_url}/api/v1/agents",
                json=payload,
                headers={"Authorization": f"Bearer {self.access_token}"}
            )
            
            data = response.json()
            
            passed = (
                response.status_code == 200 and
                data.get("success") == True
            )
            
            if passed:
                self.agent_id = data["data"]["agent_id"]
            
            self.log_test("Agent Creation", passed)
            return passed
        except Exception as e:
            self.log_test("Agent Creation", False, str(e))
            return False
    
    async def test_agent_export_import(self) -> bool:
        """测试 Agent 导入导出"""
        try:
            # 导出 Agent
            export_response = await self.client.post(
                f"{self.base_url}/api/v1/agents/{self.agent_id}/export",
                headers={"Authorization": f"Bearer {self.access_token}"}
            )
            
            export_data = export_response.json()
            
            if export_response.status_code != 200 or not export_data.get("success"):
                self.log_test("Agent Export/Import", False, "Export failed")
                return False
            
            # 导入 Agent（模拟）
            import_payload = {
                "code": export_data["data"]["code"]
            }
            
            import_response = await self.client.post(
                f"{self.base_url}/api/v1/agents/import",
                json=import_payload,
                headers={"Authorization": f"Bearer {self.access_token}"}
            )
            
            import_data = import_response.json()
            
            passed = (
                import_response.status_code == 200 and
                import_data.get("success") == True and
                "agent_config" in import_data["data"]
            )
            
            self.log_test("Agent Export/Import", passed)
            return passed
        except Exception as e:
            self.log_test("Agent Export/Import", False, str(e))
            return False
    
    async def test_knowledge_base_creation(self) -> bool:
        """测试知识库创建"""
        try:
            payload = {
                "name": f"P0 Test KB {datetime.now().timestamp()}",
                "description": "Test knowledge base for P0 validation",
                "chunk_size": 512,
                "chunk_overlap": 128,
                "is_public": False
            }
            
            response = await self.client.post(
                f"{self.base_url}/api/v1/knowledge-bases",
                json=payload,
                headers={"Authorization": f"Bearer {self.access_token}"}
            )
            
            data = response.json()
            
            passed = (
                response.status_code == 200 and
                data.get("success") == True
            )
            
            if passed:
                self.kb_id = data["data"]["kb_id"]
            
            self.log_test("Knowledge Base Creation", passed)
            return passed
        except Exception as e:
            self.log_test("Knowledge Base Creation", False, str(e))
            return False
    
    async def test_draft_system(self) -> bool:
        """测试草稿系统"""
        try:
            # 保存草稿
            payload = {
                "name": f"P0 Draft Agent {datetime.now().timestamp()}",
                "description": "Draft for testing",
                "system_prompt": "Draft test prompt",
                "model_id": "qwen-plus",
                "temperature": 70,
                "top_p": 90
            }
            
            save_response = await self.client.post(
                f"{self.base_url}/api/v1/agents/draft",
                json=payload,
                headers={"Authorization": f"Bearer {self.access_token}"}
            )
            
            save_data = save_response.json()
            
            if save_response.status_code != 200 or not save_data.get("success"):
                self.log_test("Draft System", False, "Save draft failed")
                return False
            
            # 获取草稿列表
            list_response = await self.client.get(
                f"{self.base_url}/api/v1/agents/draft",
                headers={"Authorization": f"Bearer {self.access_token}"}
            )
            
            list_data = list_response.json()
            
            passed = (
                list_response.status_code == 200 and
                list_data.get("success") == True and
                len(list_data["data"]["drafts"]) > 0
            )
            
            self.log_test("Draft System", passed)
            return passed
        except Exception as e:
            self.log_test("Draft System", False, str(e))
            return False
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """运行所有测试"""
        print("\n" + "=" * 70)
        print("AgentNex Platform - P0 Stage Validation")
        print("=" * 70 + "\n")
        
        # 运行测试
        await self.test_health_check()
        await self.test_user_registration()
        await self.test_user_login()
        await self.test_token_auth()
        await self.test_team_creation()
        await self.test_team_invitation()
        await self.test_agent_creation()
        await self.test_agent_export_import()
        await self.test_knowledge_base_creation()
        await self.test_draft_system()
        
        # 统计结果
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r["passed"])
        failed_tests = total_tests - passed_tests
        
        # 打印结果
        print("\n" + "=" * 70)
        print("Test Results Summary")
        print("=" * 70)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests / total_tests * 100):.1f}%")
        print("=" * 70)
        
        if failed_tests > 0:
            print("\nFailed Tests:")
            for result in self.test_results:
                if not result["passed"]:
                    print(f"  - {result['test']}: {result['details']}")
        
        print("\n" + "=" * 70)
        if passed_tests == total_tests:
            print("✅ All P0 validation tests passed!")
        else:
            print(f"❌ {failed_tests} test(s) failed")
        print("=" * 70 + "\n")
        
        return {
            "total": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "success_rate": passed_tests / total_tests * 100,
            "results": self.test_results
        }


async def main():
    """主函数"""
    # 获取 Base URL
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    
    print(f"Testing against: {base_url}\n")
    
    validator = P0Validator(base_url)
    
    try:
        results = await validator.run_all_tests()
        
        # 保存结果到文件
        with open("p0_validation_results.json", "w") as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\nResults saved to: p0_validation_results.json")
        
        # 返回退出码
        sys.exit(0 if results["failed"] == 0 else 1)
        
    finally:
        await validator.close()


if __name__ == "__main__":
    asyncio.run(main())
