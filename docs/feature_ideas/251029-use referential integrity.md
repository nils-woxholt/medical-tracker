# use referential integrity

## Symptoms

- Add a symptom type setup page, similar to the medications page
- a user can set up a name, default severity and default impact
- Symptom logs should do a lookup to te symptom type and show a searchable dropdown
- the symptom logs table should change to reflect the use of the symptom type id
- also move the end date time entry to a back-end only field, it doesn;t have to be captured rather infer it from the duration minutes field.
- improve the ui for duration minutes to allow for minutes(default) and hours

## medication

- medication logs should do a lookup to the medications table and show a searchable dropdown
- the medication logs table should change to reflect the use of the medication id
