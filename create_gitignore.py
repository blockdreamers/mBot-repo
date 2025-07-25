#!/usr/bin/env python3
# -*- coding: utf-8 -*-

def create_gitignore():
    gitignore_content = """# Question Bank Files (CR 문제 데이터)
questionbank/

# Environment Variables
.env
.env.local
.env.production
.env.development

# Node.js Dependencies
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
package-lock.json

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Logs
logs/
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*
lerna-debug.log*

# Runtime data
pids/
*.pid
*.seed
*.pid.lock

# Coverage directory used by tools like istanbul
coverage/
*.lcov

# Temporary folders
tmp/
temp/

# IDE/Editor files
.vscode/
.idea/
*.swp
*.swo
*~
.sublime-workspace
.sublime-project

# OS generated files
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db
desktop.ini

# Backup files created by scripts
*.backup_*
*.bak

# Database files (if any)
*.db
*.sqlite
*.sqlite3

# Local server files
.netlify/
.vercel/

# Serverless directories
.serverless/
"""

    try:
        with open('.gitignore', 'w', encoding='utf-8') as f:
            f.write(gitignore_content)
        print("✅ .gitignore 파일이 성공적으로 생성되었습니다!")
        
        # 내용 확인
        print("\n📋 생성된 .gitignore 내용:")
        with open('.gitignore', 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
            for i, line in enumerate(lines[:20], 1):  # 처음 20줄만 표시
                print(f"{i:2d}: {line}")
            if len(lines) > 20:
                print(f"... (총 {len(lines)}줄)")
                
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    create_gitignore() 