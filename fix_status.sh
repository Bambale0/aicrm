#!/bin/bash
# Simple script to fix status.sh

awk '
BEGIN { in_telegram=0; processed_telegram=0 }
/# Проверка Telegram бота/ { in_telegram=1; print; next }
/# Проверка Email сервиса/ { if (in_telegram) processed_telegram=1; in_telegram=0 }
in_telegram && /echo -e "\$\{GREEN\}✅ Настроен\$\{NC\}"/ {
    print "        if echo \"$stats\" | grep -q \"\\\"bot_running\\\":true\"; then"
    print "            echo -e \"${GREEN}✅ Запущен${NC}\""
    print "        elif echo \"$stats\" | grep -q \"\\\"\"bot_running\\\":false\\\"\"; then"
    print "            echo -e \"${YELLOW}⚠️  Настроен, но не запущен${NC}\""
    print "        else"
    print "            echo -e \"${BLUE}ℹ️  Настроен${NC}\""
    print "        fi"
    next
}
in_telegram == 0 || processed_telegram { print }
' status.sh > status_fixed.sh

mv status_fixed.sh status.sh
chmod +x status.sh
