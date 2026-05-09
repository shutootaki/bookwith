#!/usr/bin/env bash
# H-18 / 1.2 / 1.3: git 履歴に過去のシークレットが混入していないかを検出する。
# ローカル開発機 / CI で `bash scripts/check-history-leaks.sh` を実行する想定。

set -euo pipefail

if ! command -v git >/dev/null 2>&1; then
  echo "git is required" >&2
  exit 1
fi

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "${REPO_ROOT}"

echo "=== gitleaks ==="
if command -v gitleaks >/dev/null 2>&1; then
  gitleaks detect \
    --config "${REPO_ROOT}/.gitleaks.toml" \
    --log-opts="--all" \
    --no-banner \
    --redact \
    --exit-code 1
else
  echo "[warn] gitleaks not installed. Falling back to git log -S grep."
fi

echo
echo "=== git log -S 簡易シークレット grep（履歴混入チェック） ==="

# 既知の prefix を全履歴で検索
PATTERNS=(
  "sk-proj-"
  "sk-ant-"
  "AIzaSy"
  "lsv2_pt_"
  "lsv2_sk_"
  "ghp_"
  "github_pat_"
  "AKIA"
  "BEGIN PRIVATE KEY"
  "BEGIN OPENSSH PRIVATE KEY"
)

EXIT=0
for p in "${PATTERNS[@]}"; do
  hits="$(git log --all -p -S "${p}" -- ':!:.003_local_temp_docs/' 2>/dev/null | grep -F "${p}" | head -5 || true)"
  if [ -n "${hits}" ]; then
    echo "[FOUND] ${p}"
    echo "${hits}" | sed 's/^/  /'
    EXIT=1
  else
    echo "[ok]    ${p}"
  fi
done

# 1.5: ローカルディスク上のオフトラック領域（.deepsec/ 等）にもシークレットが残置されていないか確認。
# git にトラックされていなくても、PC 紛失・誤コピー時の流出経路になる。
# `.deepsec/data/**/*.env*.json` には DeepSec のファイルスナップショットが入る運用 → ここに実キーが残ったまま
# になっているケースを検出する。
echo
echo "=== ローカル disk grep（オフトラック領域） ==="
LOCAL_DIRS=(
  ".deepsec"
)
for dir in "${LOCAL_DIRS[@]}"; do
  if [ ! -d "${dir}" ]; then
    echo "[skip]  ${dir} (not present)"
    continue
  fi
  for p in "${PATTERNS[@]}"; do
    # node_modules / dist / build 等のライブラリ内蔵サンプルは false positive。実 secret が落ちる場所だけ走査する。
    matches="$(grep -RIl --binary-files=without-match \
      --exclude-dir=node_modules \
      --exclude-dir=dist \
      --exclude-dir=build \
      --exclude-dir=.next \
      --exclude-dir=.turbo \
      --exclude-dir=__pycache__ \
      -E -- "${p}" "${dir}" 2>/dev/null || true)"
    if [ -n "${matches}" ]; then
      echo "[FOUND] ${dir} contains pattern '${p}' in:"
      echo "${matches}" | sed 's/^/  /'
      echo "  → ローテートしたあと、当該ファイルを削除または sanitize してください。"
      EXIT=1
    fi
  done
done

exit "${EXIT}"
