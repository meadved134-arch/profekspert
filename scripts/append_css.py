css_append = '''

/* ==========================================================================
   COOKIE CONSENT BANNER (152-FZ COMPLIANCE)
   ========================================================================== */
.cookie-banner {
  position: fixed;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%) translateY(160%);
  width: calc(100% - 48px);
  max-width: 960px;
  background: rgba(2, 2, 3, 0.97);
  color: #ffffff;
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.15);
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.4);
  padding: 18px 24px;
  z-index: 1500;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  transition: transform 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}

.cookie-banner.show {
  transform: translateX(-50%) translateY(0);
}

.cookie-banner-text {
  font-size: 13px;
  line-height: 1.5;
  color: #e0e0e0;
}

.cookie-banner-text a {
  color: #ffffff;
  text-decoration: underline;
  text-underline-offset: 3px;
  font-weight: 500;
  transition: opacity 0.2s;
}

.cookie-banner-text a:hover {
  opacity: 0.8;
}

.cookie-banner-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

.cookie-btn-accept {
  background: #ffffff;
  color: #020203;
  border: 1px solid #ffffff;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  padding: 10px 22px;
  cursor: pointer;
  border-radius: 0px;
  transition: all 0.2s ease;
}

.cookie-btn-accept:hover {
  background: #e5e5e5;
  transform: translateY(-1px);
}

@media (max-width: 768px) {
  .cookie-banner {
    bottom: 12px;
    width: calc(100% - 24px);
    flex-direction: column;
    align-items: stretch;
    padding: 16px;
    gap: 14px;
  }
  .cookie-btn-accept {
    width: 100%;
    text-align: center;
    padding: 12px;
  }
}

/* ==========================================================================
   FORM AGREEMENT CHECKBOX (152-FZ)
   ========================================================================== */
.form-agreement {
  margin-top: 14px;
  margin-bottom: 20px;
}

.checkbox-label {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  cursor: pointer;
  font-size: 12px;
  line-height: 1.5;
  color: var(--color-secondary);
}

.checkbox-label input[type=\"checkbox\"] {
  width: 16px;
  height: 16px;
  margin-top: 2px;
  accent-color: var(--color-primary);
  flex-shrink: 0;
  cursor: pointer;
}

.checkbox-label a {
  color: var(--color-primary);
  text-decoration: underline;
  text-underline-offset: 2px;
  font-weight: 500;
}

.checkbox-label a:hover {
  color: var(--color-hover);
}

.footer-legal-links {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.footer-legal-links a {
  color: var(--color-muted);
  text-decoration: none;
  transition: color 0.2s ease;
}

.footer-legal-links a:hover {
  color: var(--color-primary);
  text-decoration: underline;
}
'''

with open('css/style.css', 'a', encoding='utf-8') as f:
    f.write(css_append)
print('Appended CSS to css/style.css')

