# Community shadcn Registries

## Dynamic Source (Always Current)

The authoritative, always-up-to-date list of all shadcn-compatible registries:

```
https://ui.shadcn.com/r/registries.json
```

Returns a JSON array of 180+ registries. Each entry: `name`, `url`, `homepage`, `description`.

**To populate components.json with all registries**, use the `/add-registries` command — it fetches this endpoint and adds every registry automatically.

**Browse online**: https://ui.shadcn.com/docs/directory

---

## Category Guide (For Quick Reference)

The tables below organize notable registries by category. This is a curated subset — the dynamic endpoint above has the complete list.

---

## Animation & Motion

| Registry | URL | Description |
|----------|-----|-------------|
| @magicui | `https://magicui.design/r` | 50+ animated components — shimmer buttons, animated beams, globe, particles, meteors, marquee |
| @aceternity | `https://ui.aceternity.com/r` | Motion-heavy effects — parallax scroll, moving border, spotlight, aurora background, 3D cards |
| @animate-ui | `https://animate-ui.com/r` | Smooth transition components — animated accordion, fade-in, slide, reveal effects |
| @cult-ui | `https://www.cult-ui.com/r` | Creative animations — flyout menus, hover reveals, morphing shapes |
| @motion-primitives | `https://motion-primitives.com/r` | Motion building blocks — transition, animate-presence, gesture primitives |
| @chamaac | `https://chamaac.com/r` | Animation effects — glow, ripple, magnetic cursor, tilt effects |

## Extended UI Components

| Registry | URL | Description |
|----------|-----|-------------|
| @originui | `https://originui.com/r` | 100+ styled component variants — buttons, inputs, cards with extra design options |
| @diceui | `https://www.diceui.com/r` | Interactive components — combobox, tags input, editable text, kanban board |
| @basecn | `https://basecn.dev/r` | Base component extensions — enhanced select, multi-select, command palette |
| @8bitcn | `https://www.8bitcn.com/r` | Retro pixel-style UI components — 8-bit buttons, pixel cards, retro badges |
| @boldkit | `https://boldkit.dev/r` | Bold design system — distinctive buttons, cards, layouts |
| @8starlabs-ui | `https://ui.8starlabs.com/r` | Additional UI components and variants |
| @cardcn | `https://cardcn.dev/r` | Card-focused components — pricing cards, profile cards, feature cards, stat cards |
| @unlumen-ui | `https://ui.unlumen.com/r` | Minimalist UI components |

## Blocks & Sections

| Registry | URL | Description |
|----------|-----|-------------|
| @bundui | `https://bundui.io/r` | Landing page blocks — hero sections, feature grids, pricing tables, testimonials |
| @blocks-so | `https://blocks.so/r` | Marketing blocks — CTA sections, navigation, footers, content sections |
| @efferd | `https://efferd.com/r` | Pre-built page sections — headers, footers, feature sections |
| @doras-ui | `https://ui.doras.to/r` | Dashboard and application blocks |
| @creative-tim | `https://www.creative-tim.com/ui/r` | Professional UI blocks — admin dashboards, landing pages, e-commerce sections |

## E-Commerce

| Registry | URL | Description |
|----------|-----|-------------|
| @commerce-ui | `https://commerce-ui.com/r` | E-commerce components — product cards, shopping cart, checkout flow, reviews, wishlists |

## AI Components

| Registry | URL | Description |
|----------|-----|-------------|
| @ai-elements | `https://ai-sdk.dev/elements/r` | Vercel AI SDK UI elements — chat interfaces, streaming response displays |
| @assistant-ui | `https://www.assistant-ui.com/r` | AI assistant UIs — chat bubbles, thread views, suggested prompts, tool call displays |
| @tool-ui | `https://www.tool-ui.com/r` | Tool/function call UIs for AI agents — tool result cards, execution status |
| @ai-blocks | `https://webllm.org/blocks/r` | WebLLM blocks — browser-based LLM interfaces, local inference UIs |

## File Upload

| Registry | URL | Description |
|----------|-----|-------------|
| @better-upload | `https://better-upload.com/r` | Upload components — drag-and-drop zones, progress indicators, file previews |

## Other

| Registry | URL | Description |
|----------|-----|-------------|
| @arc | `https://witharc.co/components/r` | Design system components |
| @abui | `https://abui.io/r` | Additional UI component library |
| @aevr | `https://ui.aevr.space/r` | UI component variants |
| @einui | `https://ui.eindev.ir/r` | Extended UI components |
| @billingsdk | `https://billingsdk.com/r` | Billing and payment form components — subscription management, plan selectors |

---

## Populating components.json

Use the `/add-registries` command to automatically fetch all 180+ registries from `https://ui.shadcn.com/r/registries.json` and add them to `components.json`.

The command:
1. Fetches the JSON endpoint
2. Parses each entry's `name` and `url`
3. Adds them to the `"registries"` field in `components.json`
4. Merges with existing entries — never overwrites
