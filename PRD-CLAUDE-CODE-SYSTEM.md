# PRD — Peta Sistem Claude Code untuk GrokBuild

**Untuk:** GrokBuild  
**Dari:** mesin Claude Code yang sudah jalan  
**Tanggal cek:** 2026-08-13  
**Status:** siap dipakai sebagai peta pasang ulang

Dokumen ini menjelaskan sistem Claude Code di mesin ini.

Bukan kode aplikasi.

Ini peta.

Peta ini supaya GrokBuild mengerti:

- apa yang terpasang
- untuk apa masing-masing
- dari mana asalnya
- bagaimana cara pasangnya

Rahasia tidak ditulis di sini.

Jangan salin token.

Jangan salin URL gateway.

Jangan salin mapping model.

---

## 1. Tujuan

GrokBuild harus bisa:

1. mengerti lapisan sistem Claude Code
2. tahu skill, MCP, plugin, CLAUDE.md, dan sistem lain
3. pasang ulang setup yang sama
4. tidak mengaktifkan semua alat sekaligus

Aturan besar:

```text
pikir dulu
  ↓
bukti di repo
  ↓
satu spesialis
  ↓
cek hasil
```

Jangan pakai alat hanya karena alat itu ada.

---

## 2. Gambar besar

Claude Code adalah program chat di terminal.

Ia bisa baca file.

Ia bisa jalanin perintah.

Ia bisa pakai alat tambahan.

Alat tambahan itu ada beberapa jenis:

| Jenis | Artinya sederhana | Tempat |
| --- | --- | --- |
| Skill | resep kerja | `~/.claude/skills/` |
| MCP | alat luar yang Claude bisa panggil | `~/.claude.json` → `mcpServers` |
| Plugin | paket dari marketplace | `~/.claude/plugins/` |
| CLAUDE.md | aturan tetap | `~/.claude/CLAUDE.md` |
| Output style | cara bicara | `~/.claude/output-styles/` |
| Runtime CSER | pemasang dan router | `~/.claude/runtime/` |
| Settings | pengaturan user | `~/.claude/settings.json` |
| Memory | catatan kecil antar sesi | `~/.claude/projects/<slug>/memory/` |

Lapisan di mesin ini, dari bawah ke atas:

```text
1. Claude Code native 2.1.229
   ~/.local/bin/claude

2. Settings user
   ~/.claude/settings.json

3. Router CSER
   ~/.claude/CLAUDE.md

4. Skill
   ~/.claude/skills/

5. MCP
   ~/.claude.json → mcpServers

6. Runtime CSER
   ~/.claude/runtime/

7. Output style ELI5
   ~/.claude/output-styles/ELI5.md

8. Memory sesi
   ~/.claude/projects/<slug>/memory/
```

Ada gateway custom.

Nama model di settings hanya alias.

Jangan tebak provider dari nama itu.

---

## 3. Claude Code sendiri

### 3.1 Apa ini

Program utamanya.

Tanpa ini, skill dan MCP tidak jalan.

### 3.2 Yang terpasang

| Item | Nilai |
| --- | --- |
| Metode pasang | native |
| Versi | `2.1.229` |
| Binary | `/home/fahmiagent/.local/bin/claude` |
| Isi binary | symlink ke `/home/fahmiagent/.local/share/claude/versions/2.1.229` |
| Sumber resmi | https://docs.claude.com/en/docs/claude-code |
| Cek | `claude --version` |

### 3.3 Cara pasang

Ikuti dokumen resmi Anthropic untuk native install.

Setelah terpasang:

```bash
claude --version
```

Hasil yang diharapkan di mesin ini:

```text
2.1.229 (Claude Code)
```

Jangan commit folder `~/.claude`.

Jangan commit token.

---

## 4. Settings

File:

```text
/home/fahmiagent/.claude/settings.json
```

File ini milik user.

CSER tidak menulis file ini.

### 4.1 Kunci yang ada

Hanya nama kunci.

Bukan nilai rahasia.

```text
env.ANTHROPIC_BASE_URL
env.ANTHROPIC_AUTH_TOKEN
env.ANTHROPIC_DEFAULT_FABLE_MODEL
env.ANTHROPIC_DEFAULT_OPUS_MODEL
env.ANTHROPIC_DEFAULT_SONNET_MODEL
env.ANTHROPIC_DEFAULT_HAIKU_MODEL
env.CLAUDE_CODE_MAX_CONTEXT_TOKENS
permissions.defaultMode = bypassPermissions
model = fable
outputStyle = ELI5
effortLevel = high
theme = dark
hasCompletedOnboarding = true
skipDangerousModePermissionPrompt = true
```

### 4.2 Artinya singkat

| Kunci | Artinya |
| --- | --- |
| `ANTHROPIC_BASE_URL` | alamat gateway. Jangan tulis nilainya di dokumen |
| `ANTHROPIC_AUTH_TOKEN` | token. Jangan tulis nilainya |
| `ANTHROPIC_DEFAULT_*_MODEL` | alias model. Jangan tebak provider dari namanya |
| `CLAUDE_CODE_MAX_CONTEXT_TOKENS` | batas konteks |
| `permissions.defaultMode` | di mesin ini `bypassPermissions` |
| `model` | alias aktif: `fable` |
| `outputStyle` | cara bicara: `ELI5` |
| `effortLevel` | `high` |

Isi settings sendiri di mesin baru.

Jangan salin token orang lain.

Jangan commit file ini.

---

## 5. CLAUDE.md

File hidup:

```text
/home/fahmiagent/.claude/CLAUDE.md
```

Sumber template:

```text
/home/fahmiagent/Downloads/LAB GITHUB/EXPERIMENTAL/claude/templates/global/CLAUDE.md
```

Dokumen routing:

```text
/home/fahmiagent/.claude/runtime/docs/routing.md
```

### 5.1 Isi singkat

- pakai tool sedikit
- bukti repo dulu
- satu spesialis utama per masalah
- Codebase Memory dulu
- Serena hanya kalau perlu
- Context7 untuk docs library
- Exa untuk riset web
- ADHD hanya keputusan sulit
- UI: Impeccable dulu
- Emil hanya untuk gerak / animasi
- BrowserAct = coba seperti user
- chrome-devtools-axi = cari sebab di browser
- Playwright = tes tetap di project
- Security / Performance hanya saat risiko cocok
- pilih profil cek: FAST, STANDARD, UI, SECURITY, PERFORMANCE, atau RELEASE
- nama model hanyalah alias jika gateway custom dipakai

### 5.2 Routing yang harus diikuti GrokBuild

```text
bukti di repo cukup?
        ↓ ya → kerjakan langsung
        ↓ tidak
Codebase Memory
        ↓ masih kurang untuk ubah simbol lintas file
Serena
        ↓ butuh docs library sekarang
Context7
        ↓ butuh riset web umum
Exa
        ↓ keputusan sulit / banyak jebakan
ADHD
        ↓ UI
Impeccable
        ↓ gerak / animasi
Emil
        ↓ coba seperti user
BrowserAct
        ↓ cari sebab di browser
chrome-devtools-axi
        ↓ jaga agar tidak rusak lagi
Playwright
        ↓ auth / secret / bayar / upload / webhook
AstralForge Security
        ↓ lambat / bundle / query / CWV
AstralForge Performance
        ↓ kerja GitHub
gh-axi
```

Jangan aktifkan semua sekali jalan.

---

## 6. CSER

Nama panjang: Claude Senior Engineering Runtime

Singkatan: CSER

Ini pemasang dan penjaga setup.

Bukan plugin Claude.

### 6.1 Folder sumber

```text
/home/fahmiagent/Downloads/LAB GITHUB/EXPERIMENTAL/claude
```

File penting di situ:

| File | Fungsi |
| --- | --- |
| `README.md` | cara pakai CSER |
| `install-claude-runtime.sh` | pemasang |
| `config/sources.json` | kunci sumber + checksum |
| `config/components.tsv` | daftar komponen |
| `config/claude-code-profile.json` | ringkasan profil full |
| `templates/global/CLAUDE.md` | template router |
| `docs/claude-code-setup.md` | panduan pasang portable |
| `skillmcp.txt` | PRD CSER yang lebih panjang |

### 6.2 Yang sudah terpasang

Runtime hidup:

```text
/home/fahmiagent/.claude/runtime/
```

Manifest:

```text
/home/fahmiagent/.claude/runtime/manifest.json
```

Mode: `full`

Perintah runtime:

```text
/home/fahmiagent/.local/bin/claude-runtime
```

### 6.3 Cara pasang

```bash
cd "/home/fahmiagent/Downloads/LAB GITHUB/EXPERIMENTAL/claude"
./install-claude-runtime.sh --full --dry-run
./install-claude-runtime.sh --full
claude-runtime doctor
```

Cek project tanpa mengubah apa pun:

```bash
claude-runtime init /path/to/project
```

Buat konteks project hanya jika belum ada:

```bash
claude-runtime init /path/to/project --apply
claude-runtime doctor --project /path/to/project
```

### 6.4 Aturan CSER

- CSER tidak menulis `~/.claude.json` langsung
- MCP dipasang lewat `claude mcp`
- CSER tidak menulis `settings.json`
- file milik CSER dicatat di manifest
- rollback hanya menyentuh yang CSER ubah
- Exa yang sudah ada dibiarkan

### 6.5 Profil verifikasi

Folder:

```text
/home/fahmiagent/.claude/runtime/profiles/
```

| Profil | Pakai kapan |
| --- | --- |
| `fast` | ubahan kecil, cek cepat |
| `standard` | fitur biasa |
| `ui` | ubahan tampilan |
| `security` | auth, secret, API, bayar |
| `performance` | lambat, bundle, query, CWV |
| `release` | mau rilis |

CWV yang dipakai sekarang: LCP, INP, CLS.

FID sudah lama. Jangan jadikan patokan utama.

### 6.6 Status komponen

Arti status CSER:

| Status | Artinya |
| --- | --- |
| `OK` / `INSTALLED` | terpasang dan jadi inti |
| `AVAILABLE` | ada, tapi tidak selalu dipakai |
| `ON_DEMAND` | hanya jika pemicu cocok |
| `SETUP_REQUIRED` | inti ada, fitur login masih perlu setup manusia |
| `NOT_EVALUATED` | dicek per project, tidak dipasang global |

---

## 7. Skill

Skill = resep.

Claude membaca `SKILL.md`, lalu mengikuti langkahnya.

Folder user:

```text
/home/fahmiagent/.claude/skills/
```

Cara pasang skill paket:

```bash
npx skills@latest add <owner>/<repo> -g -a claude-code
```

Cek skill global:

```bash
npx skills@latest ls -g -a claude-code
```

CLI skill yang dikunci CSER: `skills@1.5.22`

---

### 7.1 Skill user yang terpasang

Ada 15 skill user.

#### Matt Pocock — alur kerja

Sumber paket:

https://github.com/mattpocock/skills

Cara pasang:

```bash
npx skills@latest add mattpocock/skills -g -a claude-code
```

| Skill | Path | Fungsi | Kapan |
| --- | --- | --- | --- |
| `ask-matt` | `~/.claude/skills/ask-matt/` | pilih alur yang cocok | user bingung mau mulai dari mana |
| `grill-with-docs` | `~/.claude/skills/grill-with-docs/` | tanya sampai rencana jelas, tulis dokumen | ada folder kerja |
| `to-spec` | `~/.claude/skills/to-spec/` | ubah obrolan jadi spec | rencana sudah cukup |
| `to-tickets` | `~/.claude/skills/to-tickets/` | pecah jadi tiket | spec sudah ada |
| `implement` | `~/.claude/skills/implement/` | kerjakan spec atau tiket | siap bangun |
| `tdd` | `~/.claude/skills/tdd/` | tes dulu, baru kode | fitur atau bug |
| `code-review` | `~/.claude/skills/code-review/` | cek standar + spec | setelah kerja |

Alur Matt:

```text
/grill-with-docs
      ↓
/to-spec
      ↓
/to-tickets
      ↓
/implement
      ↓
/tdd
      ↓
/code-review
```

Matt tidak menggantikan security, performance, atau desain visual jika spesialis itu memang dibutuhkan.

#### ADHD

| Item | Nilai |
| --- | --- |
| Path | `~/.claude/skills/adhd/` |
| Fungsi | cari banyak jawaban, buang jebakan |
| Status | ON_DEMAND |
| Sumber | https://github.com/UditAkhourii/adhd |
| Revisi CSER | `3d9dc487bc2eba4449742e2db0d92be9ebdf95b6` |
| Tree | `skills/adhd` |

Pakai untuk keputusan sulit, desain API, skema, atau debug kabur.

Jangan pakai untuk typo, CRUD biasa, atau bug yang sebabnya sudah jelas.

Panggil:

```text
/adhd <masalah>
```

#### Impeccable

| Item | Nilai |
| --- | --- |
| Path | `~/.claude/skills/impeccable/` |
| Fungsi | desain dan poles UI |
| Versi | `4.0.4` |
| Status | AVAILABLE |
| Sumber | https://github.com/pbakaus/impeccable |
| Revisi CSER | `9a949fb543d44cfb406f61bcab99d95d7f12cf1d` |
| Tree | `.claude/skills/impeccable` |

Pakai untuk tampilan.

Jangan pakai untuk kerja backend saja.

#### Emil Design Engineering

| Item | Nilai |
| --- | --- |
| Path | `~/.claude/skills/emil-design-eng/` |
| Fungsi | animasi, transisi, gerak |
| Sumber | https://github.com/emilkowalski/skills |
| Referensi | https://animations.dev/ |

Cara pasang:

```bash
npx skills@latest add emilkowalski/skills -g -a claude-code
```

Pakai hanya jika ada gerak.

Impeccable dulu. Emil belakangan.

#### BrowserAct

| Item | Nilai |
| --- | --- |
| Path | `~/.claude/skills/browser-act/` |
| Fungsi | buka browser seperti user |
| Skill sumber | https://github.com/browser-act/skills |
| Situs | https://www.browseract.com |
| CLI | `browser-act` `1.3.0` |
| Paket | `browser-act-cli` |
| Cara CLI | `uv tool install browser-act-cli --python 3.12` |

Jangan jalankan perintah `browser-act` langsung lewat Bash mentah.

Panggil skill dulu.

Fitur yang butuh login masih `SETUP_REQUIRED`.

Inti lokal tetap bisa dipakai.

#### chrome-devtools-axi

| Item | Nilai |
| --- | --- |
| Path | `~/.claude/skills/chrome-devtools-axi/` |
| Fungsi | debug Chrome: klik, isi form, network, console |
| Sumber | https://github.com/kunchenguid/chrome-devtools-axi |
| Cara jalan | `npx -y chrome-devtools-axi <command>` |

Cara pasang skill:

```bash
npx skills@latest add kunchenguid/chrome-devtools-axi -g -a claude-code
```

Pakai jika sudah ada masalah di browser.

Jangan pakai jika `curl` sudah cukup.

#### gh-axi

| Item | Nilai |
| --- | --- |
| Path | `~/.claude/skills/gh-axi/` |
| Fungsi | kerja GitHub: issue, PR, Actions, release |
| Sumber | https://github.com/kunchenguid/gh-axi |
| Butuh | `gh` sudah login |
| Cara `gh` | https://cli.github.com/ |
| Cara jalan | `npx -y gh-axi <command>` |

Cara pasang skill:

```bash
npx skills@latest add kunchenguid/gh-axi -g -a claude-code
```

Kalau `gh` belum login, minta manusia jalankan:

```bash
gh auth login
```

#### AstralForge Security

| Item | Nilai |
| --- | --- |
| Skill | `full-audit-keamanan` |
| Path | `~/.claude/skills/full-audit-keamanan/` |
| Fungsi | audit keamanan defensif |
| Status | ON_DEMAND |
| Sumber | https://github.com/kuker24/AstralForge-Senior-Engineer-Skills |
| Tree | `installer/skills/full-audit-keamanan` |
| Revisi CSER | `69bce2de8d24a23792a3b87114f11c7d52737efb` |

Pakai hanya jika ada auth, hak akses, secret, API, bayar, upload, webhook, atau operasi istimewa.

#### AstralForge Performance

| Item | Nilai |
| --- | --- |
| Skill | `full-performance-audit` |
| Path | `~/.claude/skills/full-performance-audit/` |
| Fungsi | audit kecepatan |
| Status | ON_DEMAND |
| Sumber | repo AstralForge yang sama |
| Tree | `installer/skills/full-performance-audit` |
| Patch CSER | `cser-modern-cwv-v1` |

Pakai hanya jika ada regresi: bundle, query, memori, latency, atau Core Web Vitals.

---

### 7.2 Skill bawaan Claude Code

Ini tidak ada di `~/.claude/skills/`.

Claude Code membawanya sendiri.

| Skill | Fungsi |
| --- | --- |
| `claude-api` | referensi API Claude / Anthropic |
| `dataviz` | grafik dan dashboard |
| `update-config` | ubah `settings.json` / hooks |
| `loop` | jalankan tugas berulang |
| `run` | jalankan aplikasi project |
| `init` | buat `CLAUDE.md` project |
| `security-review` | review keamanan perubahan |
| `simplify` | sederhanakan kode yang baru diubah |
| `fewer-permission-prompts` | kurangi prompt izin |
| `keybindings-help` | atur shortcut |
| `artifact-design` | desain halaman Artifact |
| `artifact-diagramming` | gambar diagram Artifact |

Jangan salin skill bawaan ke folder user.

---

## 8. MCP

MCP = alat luar.

Claude memanggilnya seperti tool.

Config hidup:

```text
/home/fahmiagent/.claude.json
```

Kunci:

```text
mcpServers
```

Jangan edit file itu dengan tangan jika CSER yang memasang.

Pakai:

```bash
claude mcp list
claude mcp add ...
claude mcp remove --scope user <nama>
```

Ada 4 MCP user.

---

### 8.1 codebase-memory-mcp

Peta repo.

Pakai ini dulu sebelum baca semua file.

| Item | Nilai |
| --- | --- |
| Tipe | stdio |
| Fungsi | arsitektur repo, pencarian simbol, dampak ubahan |
| Status CSER | INSTALLED / default |
| Versi | `0.9.0` |
| Sumber | https://github.com/DeusData/codebase-memory-mcp |
| Revisi | `b637e3330c96cfe452da623db068c241aaa3ec01` |
| Artifact | `https://github.com/DeusData/codebase-memory-mcp/releases/download/v0.9.0/codebase-memory-mcp-linux-amd64-portable.tar.gz` |
| Binary | `/home/fahmiagent/.claude/runtime/components/codebase-memory/bin/codebase-memory-mcp` |

CSER yang memasang binary.

Lalu MCP didaftarkan lewat `claude mcp add`.

Jangan pasang hook / agent / skill upstream Codebase Memory.

Hanya binary + MCP.

---

### 8.2 context7

Docs library yang masih baru.

| Item | Nilai |
| --- | --- |
| Tipe | http |
| URL | `https://mcp.context7.com/mcp` |
| Fungsi | dokumentasi framework / library sekarang |
| Status | AVAILABLE / on demand |
| Sumber | https://github.com/upstash/context7 |

Pasang:

```bash
claude mcp add --scope user --transport http context7 https://mcp.context7.com/mcp
```

Pakai hanya jika bukti di repo tidak cukup.

Jangan pakai untuk konsep pemrograman umum.

---

### 8.3 exa

Cari di web.

| Item | Nilai |
| --- | --- |
| Tipe | http |
| URL | `https://mcp.exa.ai/mcp` |
| Fungsi | riset web di luar docs library |
| Status | preexisting, CSER biarkan |

Pasang:

```bash
claude mcp add --scope user --transport http exa https://mcp.exa.ai/mcp
```

Pakai setelah Context7 tidak cocok.

Atau jika topiknya bukan docs library.

---

### 8.4 serena

Ubah kode per simbol.

| Item | Nilai |
| --- | --- |
| Tipe | stdio |
| Fungsi | cari simbol, rename, edit tepat |
| Status | ON_DEMAND |
| Versi | `1.6.1` |
| Sumber | https://github.com/oraios/serena |
| Revisi | `bcac0969fb8685783ea6d0f2642468fcc47e6395` |
| Paket | `serena-agent` |
| Binary | `/home/fahmiagent/.local/bin/serena` |

Pasang CLI:

```bash
uv tool install serena-agent
```

Daftar MCP:

```bash
claude mcp add --scope user serena -- serena start-mcp-server --context claude-code --project-from-cwd --open-web-dashboard false
```

Perintah yang terpasang persis:

```text
serena start-mcp-server --context claude-code --project-from-cwd --open-web-dashboard false
```

Pakai hanya setelah Codebase Memory tidak cukup untuk ubahan semantik yang tepat.

Jangan jadikan Serena dan Codebase Memory sebagai otak utama di saat yang sama.

Sebelum kerja kode dengan Serena, baca manualnya lewat tool `initial_instructions`.

---

## 9. Plugin

Marketplace resmi ter-cache di:

```text
/home/fahmiagent/.claude/plugins/marketplaces/claude-plugins-official
```

Sumber:

https://github.com/anthropics/claude-plugins-official

Catatan cache:

```text
/home/fahmiagent/.claude/plugins/known_marketplaces.json
```

### 9.1 Yang aktif

Tidak ada plugin user yang terpasang sebagai paket aktif.

Yang tercatat:

```text
anthropic-skills@inline
```

Itu bawaan.

Bukan plugin tambahan yang kita pasang.

### 9.2 Yang tidak boleh dilakukan

Jangan pasang semua plugin di marketplace.

Sistem ini pakai skill + MCP.

Bukan tumpukan plugin.

Folder marketplace hanya cache.

Isinya banyak contoh resmi. Itu bukan berarti semuanya dipakai.

---

## 10. Sistem lain

### 10.1 Output style ELI5

File:

```text
/home/fahmiagent/.claude/output-styles/ELI5.md
```

Aktif lewat settings:

```text
outputStyle = ELI5
```

Isinya: bicara sederhana.

Kalimat pendek.

Kasih tahu:

- apa yang dilakukan
- berhasil atau tidak
- apa yang perlu dilakukan sekarang

Kalau ada pilihan, maksimal dua.

Sebutkan yang direkomendasikan.

Path dan perintah harus persis.

### 10.2 Memory

Folder sesi project:

```text
/home/fahmiagent/.claude/projects/<slug-project>/memory/
```

Index:

```text
MEMORY.md
```

Satu fakta satu file.

Jangan simpan secret.

Jangan simpan yang sudah ada di git.

### 10.3 Hooks

Tidak ada hook user di `~/.claude`.

Jangan menambah hook kecuali user minta.

### 10.4 Agents user

Tidak ada folder:

```text
~/.claude/agents
```

Beberapa skill Matt punya file `agents/openai.yaml` di dalam skill.

Itu milik skill.

Bukan agent global.

### 10.5 Binary bantu

| Perintah | Fungsi | Sumber |
| --- | --- | --- |
| `uv` | pasang tool Python | https://docs.astral.sh/uv/ |
| `npx` | jalankan paket Node | Node.js / nvm |
| `gh` | GitHub CLI | https://cli.github.com/ |
| `semgrep` | scan keamanan statis | https://semgrep.dev/ |
| `osv-scanner` | scan celah dependensi | https://google.github.io/osv-scanner/ |
| `gitleaks` | cari secret | https://github.com/gitleaks/gitleaks |
| `pre-commit` | jalankan hook project | https://pre-commit.com/ |

Di mesin ini:

```text
uv tool list
  browser-act-cli v1.3.0
  serena-agent v1.6.1
```

Node yang terlihat saat cek:

```text
/home/fahmiagent/.nvm/versions/node/v24.18.0/bin/npx
```

### 10.6 Capability per project

Ini tidak dipasang global.

CSER hanya mendeteksi jika ada di project.

| Nama | Sumber | Artinya |
| --- | --- | --- |
| Playwright | https://playwright.dev/ | tes browser tetap |
| TypeScript | https://www.typescriptlang.org/ | cek tipe |
| Vitest | https://vitest.dev/ | tes unit |
| Coverage | project-local | cakupan tes |
| Knip | https://knip.dev/ | kode / export mati |

Jangan klaim tool ini ada jika project tidak memilikinya.

---

## 11. Peta tanggung jawab

Supaya GrokBuild tidak dobel kerja.

| Kerjaan | Yang dipakai | Jangan ganti dengan |
| --- | --- | --- |
| pilih alur | ask-matt | semua skill sekaligus |
| rencanakan fitur | grill-with-docs → to-spec → to-tickets | ADHD untuk kerja biasa |
| tulis kode | implement + tdd | Serena dulu |
| pahami repo | Codebase Memory | baca semua file |
| rename besar | Serena | grep mentah saja |
| docs library | Context7 | Exa |
| riset web | Exa | Context7 |
| UI | Impeccable | Emil |
| animasi | Emil | Impeccable saja |
| coba seperti user | BrowserAct | chrome-devtools-axi |
| debug browser | chrome-devtools-axi | BrowserAct |
| tes tetap | Playwright project | BrowserAct |
| GitHub | gh-axi | plugin GitHub marketplace |
| keamanan | full-audit-keamanan + semgrep / osv / gitleaks | tebak tanpa bukti |
| kecepatan | full-performance-audit | skill UI |

---

## 12. Urutan pasang ulang

Ikuti urutan ini di mesin baru.

### Langkah 1 — Claude Code

Pasang Claude Code native.

Cek:

```bash
claude --version
```

### Langkah 2 — Settings

Isi `~/.claude/settings.json` sendiri.

Jangan salin token.

Jangan commit file itu.

### Langkah 3 — Alat dasar

Pastikan ada:

```bash
uv --version
node --version
npx --version
gh --version
```

Login GitHub jika perlu:

```bash
gh auth login
```

### Langkah 4 — CSER

Pakai folder sumber:

```text
/home/fahmiagent/Downloads/LAB GITHUB/EXPERIMENTAL/claude
```

Lalu:

```bash
cd "/home/fahmiagent/Downloads/LAB GITHUB/EXPERIMENTAL/claude"
./install-claude-runtime.sh --full --dry-run
./install-claude-runtime.sh --full
claude-runtime doctor
```

CSER akan:

- menulis router `~/.claude/CLAUDE.md` jika itu miliknya
- memasang skill owned
- memasang binary Codebase Memory
- memasang Serena lewat `uv`
- mendaftarkan MCP lewat `claude mcp`

### Langkah 5 — Cek MCP

```bash
claude mcp list
```

Harus ada:

```text
codebase-memory-mcp
context7
exa
serena
```

Jika Exa atau Context7 belum ada:

```bash
claude mcp add --scope user --transport http context7 https://mcp.context7.com/mcp
claude mcp add --scope user --transport http exa https://mcp.exa.ai/mcp
```

### Langkah 6 — Cek skill

```bash
ls /home/fahmiagent/.claude/skills
```

Harus ada 15 nama ini:

```text
adhd
ask-matt
browser-act
chrome-devtools-axi
code-review
emil-design-eng
full-audit-keamanan
full-performance-audit
gh-axi
grill-with-docs
impeccable
implement
tdd
to-spec
to-tickets
```

Jika paket Matt / Emil / AXI belum ada, pasang dengan `npx skills@latest add ...` seperti tabel di atas.

### Langkah 7 — Output style

Pastikan file ini ada:

```text
~/.claude/output-styles/ELI5.md
```

Dan settings memakai:

```text
outputStyle = ELI5
```

### Langkah 8 — Jangan commit ini

```text
~/.claude/settings.json
~/.claude.json
token
kunci API
profil OAuth
data transaksi CSER
profil browser
```

---

## 13. Perintah pasang per komponen

Salin yang ini jika CSER tidak dipakai, atau jika satu bagian hilang.

### Skill paket

```bash
npx skills@latest add mattpocock/skills -g -a claude-code
npx skills@latest add emilkowalski/skills -g -a claude-code
npx skills@latest add kunchenguid/chrome-devtools-axi -g -a claude-code
npx skills@latest add kunchenguid/gh-axi -g -a claude-code
```

### CLI Python

```bash
uv tool install browser-act-cli --python 3.12
uv tool install serena-agent
```

### MCP HTTP

```bash
claude mcp add --scope user --transport http context7 https://mcp.context7.com/mcp
claude mcp add --scope user --transport http exa https://mcp.exa.ai/mcp
```

### MCP Serena

```bash
claude mcp add --scope user serena -- serena start-mcp-server --context claude-code --project-from-cwd --open-web-dashboard false
```

### Codebase Memory

Jangan unduh sembarang.

Pakai kunci di:

```text
/home/fahmiagent/Downloads/LAB GITHUB/EXPERIMENTAL/claude/config/sources.json
```

Artifact yang dikunci:

```text
https://github.com/DeusData/codebase-memory-mcp/releases/download/v0.9.0/codebase-memory-mcp-linux-amd64-portable.tar.gz
```

Letakkan binary di:

```text
~/.claude/runtime/components/codebase-memory/bin/codebase-memory-mcp
```

Lalu daftarkan lewat `claude mcp add`.

Lebih aman: biarkan CSER yang memasang.

---

## 14. Sumber kunci CSER

File:

```text
/home/fahmiagent/Downloads/LAB GITHUB/EXPERIMENTAL/claude/config/sources.json
```

Ringkasan:

| Komponen | Repo | Versi / revisi |
| --- | --- | --- |
| codebase-memory | https://github.com/DeusData/codebase-memory-mcp | `0.9.0` / `b637e333` |
| serena | https://github.com/oraios/serena | `1.6.1` / `bcac0969` |
| adhd | https://github.com/UditAkhourii/adhd | `3d9dc487` |
| impeccable | https://github.com/pbakaus/impeccable | `4.0.4` / `9a949fb5` |
| browseract | https://github.com/browser-act/skills | tree `4577dc5a`, CLI `1.3.0` |
| astralforge-security | https://github.com/kuker24/AstralForge-Senior-Engineer-Skills | `69bce2de` |
| astralforge-performance | repo yang sama + patch `cser-modern-cwv-v1` | `69bce2de` |

Checksum ada di `sources.json`.

Pakai file itu, jangan tebak.

---

## 15. Yang tidak boleh

- Jangan tulis secret di PRD, README, atau git
- Jangan tebak provider dari nama model
- Jangan aktifkan semua tool sekaligus
- Jangan pakai Serena sebelum Codebase Memory
- Jangan pakai ADHD untuk kerja biasa
- Jangan pasang semua plugin marketplace
- Jangan edit `~/.claude.json` dengan tangan jika CSER yang menjaga MCP
- Jangan commit `settings.json`
- Jangan klaim Playwright / TypeScript / Vitest ada jika project tidak memilikinya
- Jangan jalankan `browser-act` lewat Bash mentah. Panggil skillnya

---

## 16. Cara GrokBuild memakai peta ini

Kalau GrokBuild diminta meniru sistem ini:

1. Baca dokumen ini dulu
2. Pasang Claude Code
3. Pasang CSER `--full`
4. Cek `claude-runtime doctor`
5. Cek 4 MCP
6. Cek 15 skill user
7. Jangan menyalin secret
8. Ikuti routing di bagian 5

Kalau GrokBuild diminta kerja di folder ini:

- jangan pasang ulang CSER tanpa diminta
- ikut `~/.claude/CLAUDE.md`
- pakai spesialis sesuai tabel bagian 11

---

## 17. Cek selesai

Dokumen ini benar jika:

- [x] menjelaskan Claude Code, CSER, skill, MCP, plugin, CLAUDE.md, settings, output style, memory
- [x] ada 15 skill user
- [x] ada 4 MCP
- [x] ada perintah install yang bisa disalin
- [x] ada sumber / URL
- [x] tidak ada token
- [x] path CSER dan `~/.claude` tertulis persis

Cek cepat di mesin:

```bash
claude --version
ls /home/fahmiagent/.claude/skills
claude mcp list
claude-runtime doctor
test -f /home/fahmiagent/.claude/CLAUDE.md
test -f /home/fahmiagent/.claude/output-styles/ELI5.md
```
