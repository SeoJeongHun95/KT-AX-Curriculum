@echo off
chcp 65001 >nul
set /p EMAIL=받을 지메일 주소를 입력하고 Enter: 
curl -s -S -X POST http://localhost:5678/webhook-test/day11-intake -H "Content-Type: application/json" -d "{\"name\":\"홍길동\",\"email\":\"%EMAIL%\",\"message\":\"주문 A-1023 배송이 언제인가요\"}"
echo.
echo (위에 JSON이 보이면 n8n이 받은 것)
pause
