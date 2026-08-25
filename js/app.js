document.addEventListener('DOMContentLoaded', () => {
  // 1. Mobile Menu Toggle
  const mobileToggle = document.getElementById('mobileToggle');
  const navMenu = document.getElementById('navMenu');

  if (mobileToggle && navMenu) {
    mobileToggle.addEventListener('click', () => {
      navMenu.classList.toggle('active');
      mobileToggle.classList.toggle('active');
    });

    // Close menu when clicking links
    document.querySelectorAll('.nav-link').forEach(link => {
      link.addEventListener('click', () => {
        navMenu.classList.remove('active');
        mobileToggle.classList.remove('active');
      });
    });
  }

  // 2. Modal Controller
  const modalOverlay = document.getElementById('modalOverlay');
  const modalCloseBtn = document.getElementById('modalCloseBtn');
  const openModalBtns = document.querySelectorAll('.js-open-modal');
  const modalTitle = document.getElementById('modalTitle');

  openModalBtns.forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const customTitle = btn.getAttribute('data-modal-title');
      if (customTitle && modalTitle) {
        modalTitle.textContent = customTitle;
      }
      if (modalOverlay) {
        modalOverlay.classList.add('active');
      }
    });
  });

  if (modalCloseBtn) {
    modalCloseBtn.addEventListener('click', () => {
      if (modalOverlay) modalOverlay.classList.remove('active');
    });
  }

  if (modalOverlay) {
    modalOverlay.addEventListener('click', (e) => {
      if (e.target === modalOverlay) {
        modalOverlay.classList.remove('active');
      }
    });
  }

  // 3. Form Submission Handling
  const leadForm = document.getElementById('leadForm');
  const toastSuccess = document.getElementById('toastSuccess');

  if (leadForm) {
    leadForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      
      const nameInput = document.getElementById('formName');
      const phoneInput = document.getElementById('formPhone');
      const companyInput = document.getElementById('formCompany');

      if (!phoneInput || !phoneInput.value.trim()) {
        alert('Пожалуйста, введите ваш телефон.');
        return;
      }

      const payload = {
        name: nameInput ? nameInput.value.trim() : 'Аноним',
        phone: phoneInput.value.trim(),
        company: companyInput ? companyInput.value.trim() : '',
        source: modalTitle ? modalTitle.textContent : 'Форма на сайте'
      };

      try {
        const response = await fetch('/api/leads', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        const result = await response.json();

        if (result.success) {
          if (toastSuccess) {
            toastSuccess.style.display = 'block';
            toastSuccess.textContent = result.message || 'Заявка успешно отправлена!';
          }
          leadForm.reset();
          setTimeout(() => {
            if (toastSuccess) toastSuccess.style.display = 'none';
            if (modalOverlay) modalOverlay.classList.remove('active');
          }, 3000);
        } else {
          alert(result.error || 'Ошибка отправки заявки.');
        }
      } catch (err) {
        if (toastSuccess) {
          toastSuccess.style.display = 'block';
          toastSuccess.textContent = 'Заявка принята! Мы свяжемся с вами.';
        }
        leadForm.reset();
        setTimeout(() => {
          if (toastSuccess) toastSuccess.style.display = 'none';
          if (modalOverlay) modalOverlay.classList.remove('active');
        }, 3000);
      }
    });
  }

  // 5. Dynamic SVG Diagram Connecting Lines
  function drawDiagramLines() {
    const container = document.getElementById('risksDiagramContainer');
    const svg = document.getElementById('diagramSvg');
    const coreNode = document.querySelector('.core-node-inner');
    const summaryCard = document.querySelector('.diagram-summary-card');
    if (!container || !svg || !coreNode) return;

    // Remove old lines, preserve defs
    const defs = svg.querySelector('defs');
    svg.innerHTML = '';
    if (defs) svg.appendChild(defs);

    // Hide SVG on small screens where grid breaks into single column
    if (window.innerWidth <= 1024) return;

    const containerRect = container.getBoundingClientRect();
    const coreRect = coreNode.getBoundingClientRect();

    const coreCenter = {
      x: coreRect.left + coreRect.width / 2 - containerRect.left,
      y: coreRect.top + coreRect.height / 2 - containerRect.top
    };

    // 1. Draw 6 incoming lines from risk cards to central node
    const cards = container.querySelectorAll('.risk-node');
    cards.forEach(card => {
      const cardRect = card.getBoundingClientRect();
      const cardCenter = {
        x: cardRect.left + cardRect.width / 2 - containerRect.left,
        y: cardRect.top + cardRect.height / 2 - containerRect.top
      };

      const angle = Math.atan2(coreCenter.y - cardCenter.y, coreCenter.x - cardCenter.x);

      const cardEdge = getRectEdgePoint(cardRect, containerRect, angle);
      const coreEdge = getRectEdgePoint(coreRect, containerRect, angle + Math.PI);

      const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
      line.setAttribute('x1', cardEdge.x);
      line.setAttribute('y1', cardEdge.y);
      line.setAttribute('x2', coreEdge.x);
      line.setAttribute('y2', coreEdge.y);
      line.setAttribute('stroke', '#020203');
      line.setAttribute('stroke-width', '2');
      line.setAttribute('marker-end', 'url(#arrowhead)');

      svg.appendChild(line);
    });

    // 2. Draw 1 outgoing line from bottom of "ВАШ БИЗНЕС" to top of summary card
    if (summaryCard) {
      const summaryRect = summaryCard.getBoundingClientRect();
      const startX = coreCenter.x;
      const startY = coreRect.bottom - containerRect.top;
      const endX = coreCenter.x;
      const endY = summaryRect.top - containerRect.top;

      if (endY > startY) {
        const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        line.setAttribute('x1', startX);
        line.setAttribute('y1', startY);
        line.setAttribute('x2', endX);
        line.setAttribute('y2', endY);
        line.setAttribute('stroke', '#020203');
        line.setAttribute('stroke-width', '2');
        line.setAttribute('marker-end', 'url(#arrowhead)');

        svg.appendChild(line);
      }
    }
  }

  function getRectEdgePoint(rect, containerRect, angle) {
    const cx = rect.left + rect.width / 2 - containerRect.left;
    const cy = rect.top + rect.height / 2 - containerRect.top;
    const w = rect.width / 2;
    const h = rect.height / 2;

    const cos = Math.cos(angle);
    const sin = Math.sin(angle);

    const factor = Math.min(
      Math.abs(w / (cos || 0.0001)),
      Math.abs(h / (sin || 0.0001))
    );

    return {
      x: cx + factor * cos,
      y: cy + factor * sin
    };
  }

  // Initial draw and resize handlers
  drawDiagramLines();
  window.addEventListener('resize', drawDiagramLines);
  setTimeout(drawDiagramLines, 100);

  // 6. Interactive Regional Map Controller
  const mapViewport = document.getElementById('mapViewport');
  const mapBadge = document.getElementById('mapBadgeOverlay');
  const regionItems = document.querySelectorAll('.region-item');
  const neighborPaths = document.querySelectorAll('.neighbor-path');
  const yaroslavlPath = document.getElementById('yaroslavlOblastPath');
  const russiaContour = document.getElementById('russiaContourPath');
  const pinRybinsk = document.getElementById('pinRybinsk');
  const pinYaroslavl = document.getElementById('pinYaroslavl');

  const mapStates = {
    rybinsk: {
      transform: 'matrix(2.3, 0, 0, 2.3, -450, -220)',
      badge: 'РЫБИНСК: ГЛАВНЫЙ ОФИС',
      action: () => {
        if (yaroslavlPath) yaroslavlPath.classList.add('active');
        if (neighborPaths) neighborPaths.forEach(p => p.classList.remove('active'));
        if (russiaContour) russiaContour.classList.remove('active');
        if (pinRybinsk) pinRybinsk.classList.add('active');
        if (pinYaroslavl) pinYaroslavl.classList.remove('active');
      }
    },
    yaroslavl: {
      transform: 'matrix(2.3, 0, 0, 2.3, -560, -310)',
      badge: 'ЯРОСЛАВЛЬ: ВЫЕЗД ЗА 1 ЧАС',
      action: () => {
        if (yaroslavlPath) yaroslavlPath.classList.add('active');
        if (neighborPaths) neighborPaths.forEach(p => p.classList.remove('active'));
        if (russiaContour) russiaContour.classList.remove('active');
        if (pinRybinsk) pinRybinsk.classList.remove('active');
        if (pinYaroslavl) pinYaroslavl.classList.add('active');
      }
    },
    oblast: {
      transform: 'matrix(1.65, 0, 0, 1.65, -250, -140)',
      badge: 'ЯРОСЛАВСКАЯ ОБЛАСТЬ: 100% ОХВАТ',
      action: () => {
        if (yaroslavlPath) yaroslavlPath.classList.add('active');
        if (neighborPaths) neighborPaths.forEach(p => p.classList.remove('active'));
        if (russiaContour) russiaContour.classList.remove('active');
        if (pinRybinsk) pinRybinsk.classList.add('active');
        if (pinYaroslavl) pinYaroslavl.classList.add('active');
      }
    },
    neighbors: {
      transform: 'matrix(1.2, 0, 0, 1.2, -60, -30)',
      badge: 'СОСЕДНИЕ РЕГИОНЫ: ВЫЕЗД ИНЖЕНЕРОВ',
      action: () => {
        if (yaroslavlPath) yaroslavlPath.classList.add('active');
        if (neighborPaths) neighborPaths.forEach(p => p.classList.add('active'));
        if (russiaContour) russiaContour.classList.remove('active');
        if (pinRybinsk) pinRybinsk.classList.add('active');
        if (pinYaroslavl) pinYaroslavl.classList.add('active');
      }
    },
    russia: {
      transform: 'matrix(0.85, 0, 0, 0.85, 60, 40)',
      badge: 'ВСЯ РОССИЯ: ДИСТАНЦИОННЫЙ ФОРМАТ',
      action: () => {
        if (yaroslavlPath) yaroslavlPath.classList.add('active');
        if (neighborPaths) neighborPaths.forEach(p => p.classList.add('active'));
        if (russiaContour) russiaContour.classList.add('active');
        if (pinRybinsk) pinRybinsk.classList.add('active');
        if (pinYaroslavl) pinYaroslavl.classList.add('active');
      }
    }
  };

  function setMapState(stateKey) {
    const config = mapStates[stateKey];
    if (!config) return;

    if (mapViewport) {
      mapViewport.style.transform = config.transform;
    }
    if (mapBadge) {
      mapBadge.textContent = config.badge;
    }

    config.action();

    regionItems.forEach(item => {
      if (item.getAttribute('data-map-state') === stateKey) {
        item.classList.add('active');
      } else {
        item.classList.remove('active');
      }
    });
  }

  regionItems.forEach(item => {
    item.addEventListener('mouseenter', () => {
      const stateKey = item.getAttribute('data-map-state');
      setMapState(stateKey);
    });

    item.addEventListener('click', () => {
      const stateKey = item.getAttribute('data-map-state');
      setMapState(stateKey);
    });
  });

  // Default initial state
  setMapState('rybinsk');

  /* ==========================================================================
     BLOG SLIDER CONTROLLER
     ========================================================================== */
  const blogSliderWrapper = document.getElementById('blogSliderWrapper');
  const blogPrevBtn = document.getElementById('blogPrevBtn');
  const blogNextBtn = document.getElementById('blogNextBtn');

  if (blogSliderWrapper && blogPrevBtn && blogNextBtn) {
    const scrollAmount = 364; // width of card (340px) + gap (24px)

    blogPrevBtn.addEventListener('click', () => {
      blogSliderWrapper.scrollBy({ left: -scrollAmount, behavior: 'smooth' });
    });

    blogNextBtn.addEventListener('click', () => {
      blogSliderWrapper.scrollBy({ left: scrollAmount, behavior: 'smooth' });
    });

    function updateSliderButtons() {
      const maxScrollLeft = blogSliderWrapper.scrollWidth - blogSliderWrapper.clientWidth;
      blogPrevBtn.disabled = blogSliderWrapper.scrollLeft <= 10;
      blogNextBtn.disabled = blogSliderWrapper.scrollLeft >= maxScrollLeft - 10;
    }

    blogSliderWrapper.addEventListener('scroll', updateSliderButtons);
    window.addEventListener('resize', updateSliderButtons);
    updateSliderButtons();
  }
});
