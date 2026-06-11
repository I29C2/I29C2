# JSON Schema per câmp de eligibilitate

Fiecare `field_name` din tabelul `eligibility_criteria` are aici un JSON Schema
care îi validează `value` la scriere (Ghid Tehnic §2.2). Adaugi un câmp nou =
adaugi un fișier `{field_name}.json` aici.

Validarea se face în `app/api/v1/validation.py` la acțiunea `corrected` și în
`app/ai/tasks.py` la scrierea extracției automate.
