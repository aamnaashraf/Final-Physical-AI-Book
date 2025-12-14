// src/components/InteractiveSection.tsx
import React from "react";

function InteractiveSection(): JSX.Element {
  const [open, setOpen] = React.useState(false);
  const [active, setActive] = React.useState(0);

  const promos = [
    {
      title: 'Quick Start Guide',
      subtitle: 'Get the essentials to run first simulations',
      excerpt:
        'Chapter preview — Learn how to setup ROS2, start a simulation, and inspect robot state. Perfect for first-time hands-on testing.',
    },
    {
      title: 'Tooling & Tips',
      subtitle: 'Tools used in course (Gazebo, Isaac)',
      excerpt:
        'Chapter preview — Practical tips for working with Gazebo and Isaac Sim, plus config notes to speed up your workflow.',
    },
    {
      title: 'Project Examples',
      subtitle: 'Real mini-projects you can complete',
      excerpt:
        'Chapter preview — Small projects that combine sensing, locomotion and simple controllers to build confidence quickly.',
    },
  ];

  // keyboard handler to make promo cards accessible
  const handleKey = (e: React.KeyboardEvent, index: number) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      setActive(index);
      setOpen(true);
    }
  };

  return (
    <section className="interactive-section container" aria-label="Interactive highlights">
      <div className="interactive-inner">
        <div className="interactive-left">
          <h3 className="interactive-heading">Quick highlights &amp; previews</h3>
          <p className="interactive-sub">Short previews and helpful tips from the textbook — open any card to view a short excerpt.</p>
        </div>

        <div className="interactive-grid">
          {promos.map((p, i) => (
            <button
              key={i}
              className={`promo-card ${active === i ? 'active' : ''}`}
              onClick={() => { setActive(i); setOpen(true); }}
              onKeyDown={(e) => handleKey(e, i)}
              aria-pressed={active === i}
              aria-label={`${p.title} — ${p.subtitle}`}
            >
              <div className="promo-icon" aria-hidden>{['📘','🛠️','🧩'][i]}</div>
              <div className="promo-body">
                <h4 className="promo-title">{p.title}</h4>
                <p className="promo-sub">{p.subtitle}</p>
              </div>
            </button>
          ))}
        </div>
      </div>

      <div className={`promo-preview ${open ? 'open' : ''}`} role="region" aria-hidden={!open} aria-expanded={open}>
        <div className="preview-inner">
          <button className="preview-close" onClick={() => setOpen(false)} aria-label="Close preview">✕</button>
          <h4 className="preview-title">{promos[active].title}</h4>
          <p className="preview-text">{promos[active].excerpt}</p>
          <div className="preview-actions">
            <a className="button button--primary" href="/docs/intro">Open full chapter</a>
            <button className="button button--secondary" onClick={() => setOpen(false)}>Dismiss</button>
          </div>
        </div>
      </div>
    </section>
  );
}

export default InteractiveSection;
