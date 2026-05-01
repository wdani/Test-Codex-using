# Codex Desktop Übergabe (PowerShell-sicher)

Diese Datei kannst du am PC öffnen und den Block unter **"Nachricht für Codex Desktop"** komplett kopieren.

---

## Nachricht für Codex Desktop

```text
Kontext:
- Repo: C:\path\to\Test-Codex-using
- Branch: work
- Shell: PowerShell (wichtig: nur Einzeiler mit ';', keine mehrzeiligen Bash-Blöcke)

Bisher erledigt (neu -> alt):
- 03c7978 Reuse precomputed domain noise in domain health
- 55dc74d Short-circuit export build when mask key is missing
- 1f8d462 Harden frontend error formatting for non-string API errors
- 5fc86b1 Handle export API failures without crashing panel

Wichtigster Review-Kontext PR #15:
- Inline-Kommentar 1: HCX_MASK_KEY vor Snapshot-Build prüfen -> erledigt
- Inline-Kommentar 2: Domain-Health soll precomputed noise nutzen, kein zweiter Attribute-Scan -> erledigt

PowerShell-Regeln:
- Nur Einzeiler verwenden
- Befehle mit ';' trennen
- Pfade immer in doppelte Anführungszeichen

Bitte jetzt folgende Schritte ausführen:
1) Repo-Status prüfen
Set-Location "C:\path\to\Test-Codex-using"; git status; git log --oneline -10

2) Review/Open TODO prüfen (falls verfügbar)
Set-Location "C:\path\to\Test-Codex-using"; git remote -v

3) Validierung laufen lassen
Set-Location "C:\path\to\Test-Codex-using"; ruff check .; pytest -q

4) Wenn weitere Review-Kommentare offen sind:
- gezielt fixen
- passenden Test ergänzen
- erneut prüfen mit: ruff check .; pytest -q

5) Danach sauber committen (Beispiel):
Set-Location "C:\path\to\Test-Codex-using"; git add -A; git commit -m "Address remaining PR #15 review feedback"

6) Abschlusszusammenfassung erstellen mit:
- Was wurde geändert
- Welche Tests liefen
- Welche Review-Kommentare sind damit geschlossen

Hinweis:
Wenn ein Command in PowerShell wegen Zeilenumbruch scheitert, denselben Inhalt als EINEN Einzeiler nochmal ausführen.
```

---

## Optional: Bash-Fallback (nur falls installiert)

```powershell
bash -lc "cd /c/path/to/Test-Codex-using && git status && ruff check . && pytest -q"
```

