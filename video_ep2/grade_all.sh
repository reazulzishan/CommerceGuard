#!/bin/zsh
# Apply one consistent grade (warm-daylight @ 0.6) to every footage <video> in a project.
for d in "$@"; do
  cd "$d" || continue
  for f in compositions/e*.html; do
    for id in $(grep -o 'id="[a-z0-9_-]*v" class="clip" src="assets/footage' "$f" | sed 's/id="\([^"]*\)".*/\1/'); do
      npx hyperframes media-treatment --project . --file "$f" --selector "#$id" --grading '{"preset":"warm-daylight","intensity":0.6}' --apply --json >/dev/null 2>&1 && echo "graded $d $id" || echo "FAILED $d $id"
    done
  done
done
