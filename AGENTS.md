# Paul Graham book

This is a Fumadocs (Next.js) app. Chapters are MDX in `content/docs`. The landing page is `app/(home)/page.tsx`.

Design and motion skills live in `.agents/skills/`. They were copied from `design-luphra` and `Luphra`. Use them when changing the book UI.

## Always apply

- `emil-design-eng` — taste, easing, duration, press feedback, no `scale(0)`, no `transition: all`
- `apple-design` — respond on press, interruptible motion, reduced motion
- `find-animation-opportunities` — animate rarely; never animate ⌘K / search / sidebar clicks
- `animation-vocabulary` — name the motion before inventing new effects
- `motion` — Motion/CSS springs and performance when JS animation is needed

## Motion tokens (book)

```css
--ease-out: cubic-bezier(0.23, 1, 0.32, 1);
--duration-press: 160ms;
--duration-ui: 220ms;
```

Animate `transform` and `opacity` only. Exit faster than enter. Respect `prefers-reduced-motion`.
