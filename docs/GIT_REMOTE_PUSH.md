# Private remote push (동준님용)
#
# 1) GitHub 또는 GitLab에서 **private** 저장소를 직접 생성하세요.
#    예: https://github.com/<username>/multi_asset_trigger_portfolio
#
# 2) 아래 URL을 실제 저장소로 바꾼 뒤 PowerShell에서 실행:
#
#    cd C:\Cursor\multi_asset_trigger_portfolio
#    git remote add origin https://github.com/<username>/multi_asset_trigger_portfolio.git
#    git push -u origin main
#
# GitLab 예:
#    git remote add origin https://gitlab.com/<username>/multi_asset_trigger_portfolio.git
#    git push -u origin main
#
# SSH를 쓰는 경우:
#    git remote add origin git@github.com:<username>/multi_asset_trigger_portfolio.git
#    git push -u origin main
#
# 참고: 이 PC의 전역 gitconfig 읽기 권한이 제한될 수 있습니다.
# push 전 `git config user.name` / `user.email`이 동작하는지 확인하세요.
