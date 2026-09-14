/**
 * quartz.config.yaml 후처리 스크립트
 * `npx quartz create` 가 만든 설정에 개인화 값을 덮어씁니다.
 * 주석을 보존하기 위해 yaml 의 Document API 를 사용합니다.
 *
 * usage: node _setup/patch-config.mjs --title "제목" --github "user/repo" --locale ko-KR
 */
import fs from "node:fs"
import path from "node:path"
import YAML from "yaml"

function arg(name, fallback = "") {
  const i = process.argv.indexOf(`--${name}`)
  return i !== -1 && process.argv[i + 1] ? process.argv[i + 1] : fallback
}

const root = process.cwd()
const configPath = path.join(root, "quartz.config.yaml")
if (!fs.existsSync(configPath)) {
  console.error("quartz.config.yaml 을 찾을 수 없습니다. `npx quartz create` 를 먼저 실행하세요.")
  process.exit(1)
}

const title = arg("title", "Knowledge Base")
const repo = arg("github", "") // "user/repo"
const locale = arg("locale", "ko-KR")

const doc = YAML.parseDocument(fs.readFileSync(configPath, "utf8"))

// ---- configuration ----
doc.setIn(["configuration", "pageTitle"], title)
doc.setIn(["configuration", "locale"], locale)
// 기본 템플릿은 Quartz 공식 사이트의 plausible 로 트래킹이 잡혀 있음 → 비활성화
doc.setIn(["configuration", "analytics"], null)

// Obsidian 작업 폴더/임시 폴더는 빌드에서 제외
const ignore = doc.getIn(["configuration", "ignorePatterns"])
const want = ["private", "templates", ".obsidian", ".trash", "_setup"]
if (YAML.isSeq(ignore)) {
  const have = ignore.toJSON()
  for (const p of want) if (!have.includes(p)) ignore.add(p)
} else {
  doc.setIn(["configuration", "ignorePatterns"], want)
}

// ---- plugins ----
const plugins = doc.get("plugins")
function findPlugin(name) {
  if (!YAML.isSeq(plugins)) return null
  return plugins.items.find((it) => {
    const src = it?.get?.("source")
    return typeof src === "string" && src.endsWith(`/${name}`)
  })
}
function enable(name, on = true) {
  const p = findPlugin(name)
  if (p) p.set("enabled", on)
  return p
}

// 문서 상단에 태그 목록 노출 (지식베이스에서 유용)
enable("tag-list", true)

// cname 플러그인은 baseUrl 의 호스트를 그대로 CNAME 파일로 내보냄.
// user.github.io/repo 형태의 project page 에서는 잘못된 커스텀 도메인이 설정되어
// 배포가 깨지므로 기본 비활성화. 실제 커스텀 도메인을 쓸 때만 다시 켜세요.
enable("cname", false)

// 사이드바에 최근 노트 5개
const recent = enable("recent-notes", true)
if (recent) {
  recent.set("options", doc.createNode({ title: "최근 노트", limit: 5, linkToMore: false, showTags: true }))
  recent.set("layout", doc.createNode({ position: "left", priority: 25 }))
}

// 푸터 링크를 본인 저장소로 교체
const footer = findPlugin("footer")
if (footer && repo) {
  footer.set(
    "options",
    doc.createNode({
      links: {
        GitHub: `https://github.com/${repo}`,
        "Powered by Quartz": "https://quartz.jzhao.xyz",
      },
    }),
  )
}

fs.writeFileSync(configPath, doc.toString(), "utf8")
console.log("quartz.config.yaml 패치 완료")
