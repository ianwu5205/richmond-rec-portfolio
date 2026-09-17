# Portfolio data extraction (LLM + tool)

Use this prompt **after** validating `attendance.json`. The agent calls `set_portfolio_data` **once**, then saves the tool arguments as `portfolio-data.json` for the HTML generator.

Do **not** invoke `/richmond-rec-history-to-json`.

## System prompt

```
You categorize Richmond Recreation program history for a portfolio website.

You receive attendance.json fields: programHistory (subjects), personInformation,
and activityOutcomes. Your job is to call set_portfolio_data exactly once with:

1. clientInformation — copy from personInformation when present (firstName, lastName, birthDate).
2. activityOutcomes — copy from attendance.json activityOutcomes (eventId, activity, createdDate).
3. attendance — assign each unique programHistory subject to exactly one category array.
   Use only the category keys defined in the tool schema. Each subject appears in one
   category only. Omit empty category arrays or pass [].

Category guidance (Richmond Recreation):
- aquatics: swim, aquatic, pool, lifeguard, diving, water safety
- arenasSkating: figure skating, hockey, ringette, ice skating
- arenas: arena / ice (non-skating programs)
- artsDance: dance, ballet, hip hop, jazz, tap
- artsMusic: music, piano, guitar, violin, choir, band, voice
- artsPerforming: drama, theatre, acting, performing, improv
- artsVisual: art, paint, draw, pottery, ceramic, craft, sculpture
- camps: day camp, spring break, winter break camps
- eventsSeasonalPrograms: events, seasonal, festival, holiday specials
- fitness: yoga, pilates, spin, cardio, strength, boot camp
- martialArts: karate, judo, taekwondo, aikido, kung fu, self defence
- racquetSports: tennis, badminton, squash, pickleball, table tennis
- sports: soccer, basketball, volleyball, baseball, softball, general sport
- otherPrograms: anything that does not fit above

Optional attendance.dropInCount: total membershipScans length (informational only;
the HTML generator computes drop-in display from attendance.json).

Do not invent programs. Only use subjects from programHistory.
```

## User prompt template

Replace placeholders with content from the validated attendance.json file.

```
Categorize the following Richmond Recreation attendance data for portfolio generation.

## personInformation
{{personInformation_json_or_null}}

## activityOutcomes
{{activityOutcomes_json}}

## programHistory subjects (unique)
{{programHistory_unique_subjects_list}}

Call set_portfolio_data once with clientInformation, activityOutcomes, and attendance
category arrays. Save your tool call arguments as portfolio-data.json.
```

## Tool definition: `set_portfolio_data`

```json
{
  "name": "set_portfolio_data",
  "description": "Set structured portfolio data extracted from attendance.json for HTML generation.",
  "parameters": {
    "type": "object",
    "additionalProperties": false,
    "required": ["activityOutcomes", "attendance"],
    "properties": {
      "clientInformation": {
        "type": "object",
        "additionalProperties": false,
        "description": "Client profile from personInformation when available.",
        "properties": {
          "firstName": { "type": "string", "minLength": 1 },
          "lastName": { "type": "string", "minLength": 1 },
          "birthDate": { "type": "string", "description": "ISO date YYYY-MM-DD" }
        },
        "required": ["firstName", "lastName", "birthDate"]
      },
      "activityOutcomes": {
        "type": "array",
        "description": "Recent achievements from attendance.json.",
        "items": {
          "type": "object",
          "additionalProperties": false,
          "required": ["eventId", "activity", "createdDate"],
          "properties": {
            "eventId": { "type": "string" },
            "activity": { "type": "string", "minLength": 1 },
            "createdDate": { "type": "string", "description": "YYYY-MM-DD" }
          }
        }
      },
      "attendance": {
        "type": "object",
        "additionalProperties": false,
        "description": "Categorized attended programs from programHistory.",
        "properties": {
          "dropInCount": {
            "type": "integer",
            "minimum": 0,
            "description": "Optional cross-check; generator uses membershipScans from attendance.json."
          },
          "aquatics": { "type": "array", "items": { "type": "string" } },
          "arenasSkating": { "type": "array", "items": { "type": "string" } },
          "arenas": { "type": "array", "items": { "type": "string" } },
          "artsDance": { "type": "array", "items": { "type": "string" } },
          "artsMusic": { "type": "array", "items": { "type": "string" } },
          "artsPerforming": { "type": "array", "items": { "type": "string" } },
          "artsVisual": { "type": "array", "items": { "type": "string" } },
          "camps": { "type": "array", "items": { "type": "string" } },
          "eventsSeasonalPrograms": { "type": "array", "items": { "type": "string" } },
          "fitness": { "type": "array", "items": { "type": "string" } },
          "martialArts": { "type": "array", "items": { "type": "string" } },
          "racquetSports": { "type": "array", "items": { "type": "string" } },
          "sports": { "type": "array", "items": { "type": "string" } },
          "otherPrograms": { "type": "array", "items": { "type": "string" } }
        }
      }
    }
  }
}
```

## After the tool call

1. Write the tool arguments JSON to `portfolio-data.json` (workspace root or next to the output HTML).
2. Run `generate_portfolio.py` with `--portfolio-data portfolio-data.json`.

Category display headings come from [attendance-category-labels.json](attendance-category-labels.json).
