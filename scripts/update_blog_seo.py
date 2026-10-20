import os
import re

blog_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "blog")

articles_meta = {
    "2026-2042.html": {
        "title": "Новые правила обучения по охране труда в 2026 году — ООО «ПрофЭксперт»",
        "desc": "Разбор изменений в порядке обучения по охране труда и проверке знаний требований ОТ в 2026 году для руководителей и специалистов предприятий.",
        "canonical": "https://profekspert.site/blog/2026-2042.html",
        "headline": "Новые правила обучения по охране труда в 2026 году",
        "date": "2026-08-25",
        "author": "Главный инженер ООО «ПрофЭксперт»"
    },
    "podgotovka-k-proverkam.html": {
        "title": "Подготовка к проверкам ГИТ и Роструда: пошаговый чек-лист — ООО «ПрофЭксперт»",
        "desc": "Пошаговое руководство по подготовке предприятия к плановым и внеплановым проверкам Государственной инспекции труда (ГИТ). Чек-лист документов.",
        "canonical": "https://profekspert.site/blog/podgotovka-k-proverkam.html",
        "headline": "Подготовка к проверкам ГИТ и Роструда: пошаговый чек-лист",
        "date": "2026-08-24",
        "author": "Ведущий аудитор ООО «ПрофЭксперт»"
    },
    "proizvodstvennaya-bezopasnost.html": {
        "title": "Производственная безопасность на предприятии: как исключить травматизм — ООО «ПрофЭксперт»",
        "desc": "Практические методы снижения производственного травматизма на предприятиях: оценка рисков, обучение персонала и регламенты безопасности.",
        "canonical": "https://profekspert.site/blog/proizvodstvennaya-bezopasnost.html",
        "headline": "Производственная безопасность на предприятии: как исключить травматизм",
        "date": "2026-08-23",
        "author": "Специалист по техбезопасности"
    }
}

metrika_code = """
  <!-- Yandex.Metrika counter -->
  <script type="text/javascript">
    (function(m,e,t,r,i,k,a){
        m[i]=m[i]||function(){(m[i].a=m[i].a||[]).push(arguments)};
        m[i].l=1*new Date();
        for (var j = 0; j < document.scripts.length; j++) {if (document.scripts[j].src === r) { return; }}
        k=e.createElement(t),a=e.getElementsByTagName(t)[0],k.async=1,k.src=r,a.parentNode.insertBefore(k,a)
    })(window, document,'script','https://mc.yandex.ru/metrika/tag.js?id=113672774', 'ym');

    ym(113672774, 'init', {clickmap:true, trackLinks:true, accurateTrackBounce:true, webvisor:true});
  </script>
  <noscript><div><img src="https://mc.yandex.ru/watch/113672774" style="position:absolute; left:-9999px;" alt="" /></div></noscript>
  <!-- /Yandex.Metrika counter -->"""

for filename, meta in articles_meta.items():
    filepath = os.path.join(blog_dir, filename)
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        continue
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    schema_json = f"""
  <!-- Schema.org Article Structured Data -->
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "Article",
    "mainEntityOfPage": {{
      "@type": "WebPage",
      "@id": "{meta['canonical']}"
    }},
    "headline": "{meta['headline']}",
    "description": "{meta['desc']}",
    "datePublished": "{meta['date']}",
    "author": {{
      "@type": "Person",
      "name": "{meta['author']}"
    }},
    "publisher": {{
      "@type": "Organization",
      "name": "ООО «ПрофЭксперт»",
      "logo": {{
        "@type": "ImageObject",
        "url": "https://profekspert.site/assets/logo_transparent.png"
      }}
    }}
  }}
  </script>"""

    new_head_content = f"""  <title>{meta['title']}</title>
  <meta name="description" content="{meta['desc']}">
  <link rel="canonical" href="{meta['canonical']}">
  <link rel="stylesheet" href="../css/style.css">{schema_json}{metrika_code}"""

    content = re.sub(r'<title>.*?</title>(\s*<meta name="description"[^>]*>)?\s*<link rel="stylesheet" href="\.\./css/style\.css">', new_head_content, content, flags=re.DOTALL)
    content = content.replace("+7-977-555-88-66", "+7-915-985-13-22").replace("+79775558866", "+79159851322")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Updated {filename}")
