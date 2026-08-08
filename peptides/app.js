function score_bar(score, class_name) {
  let html = `<div class="score_bar ${class_name}">`;
  for (let i = 1; i <= 5; ++i) html += `<span class="score_segment ${i <= score ? 'active' : ''}"></span>`;
  return html + '</div>';
}
function render_claim(claim) {
  const studies = claim.study_ids.map((study_id) => {
    const study = peptide_data.studies[study_id];
    const source = peptide_data.sources[study.source_id];
    return `<article class="study_row"><div><div class="study_type">${study.type} · ${study.year}</div><strong>${study.title}</strong><div class="study_population">${study.population}</div></div><a href="${source.url}" target="_blank" rel="noreferrer">Source ↗</a></article>`;
  }).join('');
  const limitations = claim.limitations.map((item) => `<li>${item}</li>`).join('');
  return `<section class="claim_card"><div class="claim_top"><div><div class="eyebrow">CLAIM</div><h3>${claim.title}</h3></div><span class="verdict">${claim.verdict}</span></div><p class="claim_explanation">${claim.explanation}</p><div class="evidence_grid"><div><div class="evidence_label"><span>Human evidence</span><strong>${claim.human_score}/5</strong></div>${score_bar(claim.human_score, 'human_bar')}</div><div><div class="evidence_label"><span>Preclinical evidence</span><strong>${claim.preclinical_score}/5</strong></div>${score_bar(claim.preclinical_score, 'preclinical_bar')}</div></div><details><summary>Why this rating?</summary><div class="details_body"><h4>Important limitations</h4><ul>${limitations}</ul><h4>Studies and assessments used</h4><div class="study_list">${studies}</div></div></details></section>`;
}
function render_sources() {
  return Object.values(peptide_data.sources).map((source) => `<a class="source_card" href="${source.url}" target="_blank" rel="noreferrer"><span>${source.label}</span><strong>${source.title}</strong><i>Open source ↗</i></a>`).join('');
}
document.getElementById('claims_container').innerHTML = peptide_data.claims.map(render_claim).join('');
document.getElementById('sources').innerHTML = render_sources();
