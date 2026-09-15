# Branding

The UI uses University of the Cordilleras' (UC) green as its primary brand
color, and the official UC seal as its logo.

## Brand color

Primary brand green: **`#09593C`**

Source: this is UC's own theme-color, taken from uc-bcf.edu.ph's site
metadata, and matches "Forest Green" as listed in UC's public Wikipedia
infobox. It is not a guess or a generic "university green."

This hex is used as the `uc-700` step of a full Tailwind color ramp defined
in `frontend/src/index.css`:

```css
@theme {
  --color-uc-50: #eaf4ef;
  --color-uc-100: #cfe6d9;
  --color-uc-200: #a3cdb8;
  --color-uc-300: #72b394;
  --color-uc-400: #46966f;
  --color-uc-500: #2c7a58;
  --color-uc-600: #1c6347;
  --color-uc-700: #09593c;  /* the real UC brand hex */
  --color-uc-800: #07452f;
  --color-uc-900: #063523;
  --color-uc-950: #042016;
}
```

Because it's a normal Tailwind theme token, it's used the same way any
other color would be: `bg-uc-800`, `text-uc-700`, `hover:bg-uc-900`, etc.
Every page in the app (`Login`, `Register`, `Dashboard`, `Opportunities`,
`Sources`, and the sidebar `Layout`) has been switched from the old
generic slate/blue palette to this ramp. A few colors were deliberately
left alone because they're functional/semantic, not brand colors:

- `emerald-700` — "OPEN" status badge
- `purple-100` / `purple-800` — Scopus / Web of Science / other indexing badges
- `amber-*` — placeholder-data warning banners
- `red-600` — form validation error text

## Logo

`frontend/src/components/Logo.jsx` renders `frontend/public/uc-logo.png` —
the official University of the Cordilleras seal (the green shield with
"UNIVERSITY OF THE CORDILLERAS · 1946"), sourced from the university's own
`UC_RESPONSIBLE_USE_OF_AI.pptx` deck (its title slide carries the seal as a
transparent-background PNG). The file shipped here was resized from the
original to 371×480px and re-optimized to keep the app light — it's a
tall seal shape, not a square icon, so `Logo.jsx` renders it with
`object-contain` inside a fixed-size box (the sidebar, login/register
cards) rather than cropping it to a circle or square.

If `uc-logo.png` is ever missing or fails to load, `Logo.jsx`
automatically falls back to a plain green circular "UC" monogram badge,
so the app never shows a broken image icon — that fallback is what
earlier builds of this app showed before the real seal was added.

**To replace it** with a different or higher-resolution version later,
overwrite:

```
frontend/public/uc-logo.png
```

and rebuild (`npm run build`) or refresh the dev server — no code changes
needed. The favicon (`frontend/index.html`) points at the same path, so
replacing that one file also updates the browser tab icon.
