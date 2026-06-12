const STOPWORDS = new Set([
  'a', 'an', 'and', 'are', 'as', 'at', 'be', 'been', 'by', 'do', 'does', 'for', 'from',
  'has', 'have', 'how', 'in', 'is', 'it', 'its', 'of', 'on', 'or', 'that', 'the', 'to',
  'was', 'were', 'what', 'when', 'which', 'who', 'with'
]);

const state = {
  apiBase: null,
  mode: 'demo',
  demoData: null,
  records: [],
  paths: {},
  currentResults: [],
  selectedSampleId: null,
  chart: null,
  cy: null,
};

const elements = {
  modeBadge: document.getElementById('modeBadge'),
  dataBadge: document.getElementById('dataBadge'),
  redisHint: document.getElementById('redisHint'),
  statsHint: document.getElementById('statsHint'),
  totalSamples: document.getElementById('totalSamples'),
  bridgeCount: document.getElementById('bridgeCount'),
  comparisonCount: document.getElementById('comparisonCount'),
  splitStats: document.getElementById('splitStats'),
  levelStats: document.getElementById('levelStats'),
  resultsList: document.getElementById('resultsList'),
  resultCount: document.getElementById('resultCount'),
  sampleDetail: document.getElementById('sampleDetail'),
  sampleMeta: document.getElementById('sampleMeta'),
  graphContainer: document.getElementById('graphContainer'),
  clusterHint: document.getElementById('clusterHint'),
  clusterList: document.getElementById('clusterList'),
  clusterChart: document.getElementById('clusterChart'),
  searchInput: document.getElementById('searchInput'),
  splitFilter: document.getElementById('splitFilter'),
  typeFilter: document.getElementById('typeFilter'),
  levelFilter: document.getElementById('levelFilter'),
  searchButton: document.getElementById('searchButton'),
};

function tokenize(text) {
  return (text.toLowerCase().match(/[a-z0-9']+/g) || [])
    .filter(function (token) { return token.length > 1 && !STOPWORDS.has(token); });
}

function escapeHtml(text) {
  return String(text)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

async function fetchJson(url) {
  var response = await fetch(url);
  if (!response.ok) {
    throw new Error('HTTP ' + response.status);
  }
  return response.json();
}

async function loadDemoData() {
  state.demoData = await fetchJson('./data/demo_samples.json');
  state.records = state.demoData.records || [];
  state.paths = state.demoData.paths || {};
}

function renderList(target, data) {
  target.innerHTML = '';
  var entries = Object.entries(data || {});
  if (!entries.length) {
    var li = document.createElement('li');
    li.textContent = '-';
    target.appendChild(li);
    return;
  }
  entries.forEach(function (_a) {
    var key = _a[0], value = _a[1];
    var li = document.createElement('li');
    li.textContent = key + ': ' + value;
    target.appendChild(li);
  });
}

function renderStats(stats) {
  elements.totalSamples.textContent = stats.total_samples != null ? stats.total_samples : 0;
  elements.bridgeCount.textContent = (stats.by_type && stats.by_type.bridge) != null ? stats.by_type.bridge : 0;
  elements.comparisonCount.textContent = (stats.by_type && stats.by_type.comparison) != null ? stats.by_type.comparison : 0;
  renderList(elements.splitStats, stats.by_split || {});
  renderList(elements.levelStats, stats.by_level || {});
  elements.statsHint.textContent = state.mode === 'api' ? '来自 Redis API（在线检索）' : '来自静态演示数据';
}

function recordMatchesFilters(record, filters) {
  return (!filters.split || record.split === filters.split)
    && (!filters.type || record.type === filters.type)
    && (!filters.level || record.level === filters.level);
}

function scoreRecord(record, queryTokens) {
  if (!queryTokens.length) {
    return 1;
  }
  var haystack = [record.question, record.answer];
  (record.context_docs || []).forEach(function (doc) {
    haystack.push(doc.title);
    haystack.push.apply(haystack, doc.sentences || []);
  });
  var tokenBag = tokenize(haystack.join(' '));
  return queryTokens.reduce(function (score, token) {
    return score + tokenBag.filter(function (item) { return item === token; }).length;
  }, 0);
}

function fuzzyMatch(record, queryTokens) {
  var lowerQuestion = record.question.toLowerCase();
  return queryTokens.some(function (token) {
    return lowerQuestion.indexOf(token) !== -1 || (record.answer && record.answer.toLowerCase().indexOf(token) !== -1);
  });
}

function localSearch(filters) {
  var queryTokens = tokenize(filters.q);
  return state.records
    .filter(function (record) { return recordMatchesFilters(record, filters); })
    .map(function (record) { return ({
      id: record.id,
      question: record.question,
      answer: record.answer,
      type: record.type,
      level: record.level,
      score: Number((scoreRecord(record, queryTokens) + (record.supporting_facts || []).length * 0.1).toFixed(2)),
    }); })
    .filter(function (record) {
      if (!queryTokens.length) return true;
      return record.score > 0 || fuzzyMatch(state.records.find(function (r) { return r.id === record.id; }), queryTokens);
    })
    .sort(function (left, right) { return right.score - left.score; })
    .slice(0, 50);
}

function jaccard(left, right) {
  if (!left.size && !right.size) {
    return 1;
  }
  if (!left.size || !right.size) {
    return 0;
  }
  var arr = [];
  left.forEach(function (t) { arr.push(t); });
  var intersection = arr.filter(function (token) { return right.has(token); }).length;
  return intersection / new Set(arr.concat(Array.from(right))).size;
}

function localCluster(sampleRecords) {
  var buckets = [];
  sampleRecords.forEach(function (record) {
    var tokenSet = new Set(tokenize(record.question));
    var bucket = null;
    for (var i = 0; i < buckets.length; i++) {
      if (jaccard(buckets[i].tokens, tokenSet) >= 0.3) {
        bucket = buckets[i];
        break;
      }
    }
    if (!bucket) {
      bucket = { tokens: new Set(), records: [], counts: {} };
      buckets.push(bucket);
    }
    bucket.records.push(record);
    tokenSet.forEach(function (token) {
      bucket.tokens.add(token);
      bucket.counts[token] = (bucket.counts[token] || 0) + 1;
    });
  });

  return buckets.map(function (bucket) {
    var keywords = Object.entries(bucket.counts)
      .sort(function (left, right) { return right[1] - left[1]; })
      .slice(0, 3)
      .map(function (_a) { return _a[0]; });
    return {
      label: keywords.join(' / ') || 'misc',
      size: bucket.records.length,
      keywords: keywords,
      sample_ids: bucket.records.map(function (record) { return record.id; }),
    };
  }).sort(function (left, right) { return right.size - left.size; });
}

function getRecordById(sampleId) {
  return state.records.find(function (record) { return record.id === sampleId; });
}

async function getSample(sampleId) {
  if (state.mode === 'api' && state.apiBase) {
    return fetchJson(state.apiBase + '/sample/' + sampleId);
  }
  return getRecordById(sampleId);
}

async function getPath(sampleId) {
  if (state.mode === 'api' && state.apiBase) {
    return fetchJson(state.apiBase + '/path/' + sampleId);
  }
  return state.paths[sampleId];
}

async function getStats() {
  if (state.mode === 'api' && state.apiBase) {
    return fetchJson(state.apiBase + '/stats');
  }
  return state.demoData.stats;
}

async function getClusters(filters) {
  if (state.mode === 'api' && state.apiBase) {
    var params = new URLSearchParams();
    if (filters.q) params.set('q', filters.q);
    if (filters.split) params.set('split', filters.split);
    if (filters.type) params.set('type', filters.type);
    if (filters.level) params.set('level', filters.level);
    return fetchJson(state.apiBase + '/cluster?' + params.toString());
  }
  var sampleRecords = state.currentResults.map(function (item) { return getRecordById(item.id); }).filter(Boolean);
  return { count: sampleRecords.length, clusters: localCluster(sampleRecords) };
}

function renderResults(results) {
  elements.resultsList.innerHTML = '';
  elements.resultCount.textContent = results.length + ' 条';

  if (!results.length) {
    elements.resultsList.innerHTML = '<div class="empty-state">没有命中结果，试试更短的关键词（如 magazine、capital、dune）。</div>';
    return;
  }

  results.forEach(function (result, index) {
    var article = document.createElement('article');
    article.className = 'result-card' + (result.id === state.selectedSampleId ? ' active' : '');
    article.innerHTML =
      '<h3>' + escapeHtml(result.question) + '</h3>' +
      '<div class="result-meta">' +
        '<span class="meta-pill">type: ' + escapeHtml(result.type) + '</span>' +
        '<span class="meta-pill">level: ' + escapeHtml(result.level) + '</span>' +
        '<span class="meta-pill">score: ' + escapeHtml(result.score) + '</span>' +
      '</div>';
    article.addEventListener('click', function () { selectSample(result.id); });
    elements.resultsList.appendChild(article);

    if (index === 0 && !state.selectedSampleId) {
      state.selectedSampleId = result.id;
    }
  });
}

function resolveSupportingSentence(sample, fact) {
  var contextDoc = (sample.context_docs || []).find(function (doc) { return doc.title === fact.title; });
  return (contextDoc && contextDoc.sentences && contextDoc.sentences[fact.sent_id]) || '未找到对应句子';
}

function renderSampleDetail(sample) {
  if (!sample) {
    elements.sampleDetail.className = 'sample-detail empty-state';
    elements.sampleDetail.textContent = '未找到样本详情';
    elements.sampleMeta.textContent = '未选择样本';
    return;
  }

  var evidenceHtml = (sample.supporting_facts || []).map(function (fact) {
    return '<div class="evidence-card">' +
      '<strong>' + escapeHtml(fact.title) + ' · sentence ' + escapeHtml(fact.sent_id) + '</strong>' +
      '<p>' + escapeHtml(resolveSupportingSentence(sample, fact)) + '</p>' +
    '</div>';
  }).join('');

  var contextHtml = (sample.context_docs || []).map(function (doc) {
    return '<div class="evidence-card">' +
      '<strong>' + escapeHtml(doc.title) + '</strong>' +
      '<p>' + escapeHtml((doc.sentences || []).join(' ')) + '</p>' +
    '</div>';
  }).join('');

  elements.sampleDetail.className = 'sample-detail';
  elements.sampleDetail.innerHTML =
    '<section><h3>Question</h3><p>' + escapeHtml(sample.question) + '</p></section>' +
    '<section><h3>Answer</h3><p>' + escapeHtml(sample.answer) + '</p></section>' +
    '<section><div class="detail-meta">' +
      '<span class="meta-pill">subset: ' + escapeHtml(sample.subset) + '</span>' +
      '<span class="meta-pill">split: ' + escapeHtml(sample.split) + '</span>' +
      '<span class="meta-pill">type: ' + escapeHtml(sample.type) + '</span>' +
      '<span class="meta-pill">level: ' + escapeHtml(sample.level) + '</span>' +
    '</div></section>' +
    '<section><h4>Supporting Facts</h4><div class="evidence-list">' + evidenceHtml + '</div></section>' +
    '<section><h4>Context 文档</h4><div class="evidence-list">' + contextHtml + '</div></section>';
  elements.sampleMeta.textContent = sample.id;
}

function graphElementsFromPayload(graph) {
  return (graph.nodes || []).map(function (node) { return { data: node }; })
    .concat((graph.edges || []).map(function (edge, index) { return { data: { id: 'edge-' + index, source: edge.source, target: edge.target, kind: edge.kind } }; }));
}

function renderGraph(graph) {
  if (!graph || !graph.nodes || !graph.nodes.length) {
    elements.graphContainer.innerHTML = '<div class="empty-state">当前样本缺少多跳图数据</div>';
    return;
  }

  elements.graphContainer.innerHTML = '';
  if (state.cy) {
    state.cy.destroy();
  }

  state.cy = cytoscape({
    container: elements.graphContainer,
    elements: graphElementsFromPayload(graph),
    layout: { name: 'breadthfirst', directed: true, padding: 18, spacingFactor: 1.25 },
    style: [
      {
        selector: 'node',
        style: {
          label: 'data(label)',
          color: '#f3f7ff',
          'font-size': 11,
          'text-wrap': 'wrap',
          'text-max-width': 140,
          'text-valign': 'center',
          'text-halign': 'center',
          width: 52,
          height: 52,
          'background-color': '#6c8cff',
          'border-width': 2,
          'border-color': '#91aaff',
        },
      },
      {
        selector: 'node[kind = "question"]',
        style: { 'background-color': '#ffcc66', 'border-color': '#ffd88c', color: '#1f2230' },
      },
      {
        selector: 'node[kind = "answer"]',
        style: { 'background-color': '#5ce1b9', 'border-color': '#82f2d0', color: '#123028' },
      },
      {
        selector: 'node[kind = "sentence"]',
        style: { 'background-color': '#263455', 'border-color': '#88a7ff', width: 88, height: 88 },
      },
      {
        selector: 'edge',
        style: {
          width: 2,
          'line-color': '#7b94ff',
          'target-arrow-color': '#7b94ff',
          'target-arrow-shape': 'triangle',
          'curve-style': 'bezier',
        },
      },
    ],
  });
}

function renderClusters(clusterPayload) {
  var clusters = clusterPayload.clusters || [];
  elements.clusterList.innerHTML = '';
  elements.clusterHint.textContent = clusters.length ? '共 ' + clusters.length + ' 个簇' : '暂无聚类结果';

  clusters.forEach(function (cluster) {
    var item = document.createElement('article');
    item.className = 'cluster-item';
    item.innerHTML =
      '<h3>' + escapeHtml(cluster.label) + '</h3>' +
      '<p>size: ' + escapeHtml(cluster.size) + ' · keywords: ' + escapeHtml((cluster.keywords || []).join(', ')) + '</p>' +
      '<p>sample ids: ' + escapeHtml((cluster.sample_ids || []).join(', ')) + '</p>';
    elements.clusterList.appendChild(item);
  });

  if (!clusters.length) {
    elements.clusterList.innerHTML = '<div class="empty-state">暂无可视化聚类数据</div>';
  }

  var labels = clusters.map(function (cluster) { return cluster.label; });
  var sizes = clusters.map(function (cluster) { return cluster.size; });

  if (state.chart) {
    state.chart.destroy();
  }

  state.chart = new Chart(elements.clusterChart, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [
        {
          label: 'Cluster Size',
          data: sizes,
          borderRadius: 10,
          backgroundColor: ['#6c8cff', '#5ce1b9', '#ffcc66', '#ff7f96', '#a990ff'],
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: {
          ticks: { color: '#dce6ff' },
          grid: { color: 'rgba(255,255,255,0.06)' },
        },
        y: {
          beginAtZero: true,
          ticks: { color: '#dce6ff', precision: 0 },
          grid: { color: 'rgba(255,255,255,0.06)' },
        },
      },
      plugins: {
        legend: { labels: { color: '#dce6ff' } },
      },
    },
  });
}

async function selectSample(sampleId) {
  state.selectedSampleId = sampleId;
  renderResults(state.currentResults);
  try {
    var results = await Promise.all([getSample(sampleId), getPath(sampleId)]);
    var sample = results[0];
    var graph = results[1];
    renderSampleDetail(sample);
    renderGraph(graph);
  } catch (e) {
    renderSampleDetail(null);
    renderGraph(null);
  }
}

function getFilters() {
  return {
    q: elements.searchInput.value.trim(),
    split: elements.splitFilter.value,
    type: elements.typeFilter.value,
    level: elements.levelFilter.value,
  };
}

async function runSearch() {
  elements.searchButton.disabled = true;
  elements.searchButton.textContent = '搜索中...';

  try {
    var filters = getFilters();
    var resultsPayload;

    if (state.mode === 'api' && state.apiBase) {
      var params = new URLSearchParams();
      if (filters.q) params.set('q', filters.q);
      if (filters.split) params.set('split', filters.split);
      if (filters.type) params.set('type', filters.type);
      if (filters.level) params.set('level', filters.level);
      resultsPayload = await fetchJson(state.apiBase + '/search?' + params.toString());
    } else {
      resultsPayload = { results: localSearch(filters) };
    }

    state.currentResults = resultsPayload.results || [];
    state.selectedSampleId = state.currentResults.length ? state.currentResults[0].id : null;
    renderResults(state.currentResults);

    if (state.selectedSampleId) {
      await selectSample(state.selectedSampleId);
    } else {
      renderSampleDetail(null);
      renderGraph(null);
    }

    var clusterPayload = await getClusters(filters);
    renderClusters(clusterPayload);
  } catch (e) {
    console.error('搜索失败:', e);
    elements.resultCount.textContent = '搜索出错';
    elements.resultsList.innerHTML = '<div class="empty-state">搜索失败: ' + escapeHtml(e.message) + '</div>';
  } finally {
    elements.searchButton.disabled = false;
    elements.searchButton.textContent = '搜索';
  }
}

async function tryDetectApi() {
  var candidates = [];
  var queryApiBase = new URLSearchParams(window.location.search).get('apiBase');
  if (queryApiBase) {
    candidates.push(queryApiBase.replace(/\/$/, ''));
  }
  if (window.HOTPOT_API_BASE) {
    candidates.push(String(window.HOTPOT_API_BASE).replace(/\/$/, ''));
  }
  candidates.push('http://127.0.0.1:8000/api');

  for (var i = 0; i < candidates.length; i++) {
    var base = candidates[i];
    try {
      var controller = new AbortController();
      var timeout = setTimeout(function () { controller.abort(); }, 1200);
      var response = await fetch(base + '/health', { signal: controller.signal });
      clearTimeout(timeout);
      if (response.ok) {
        var payload = await response.json();
        if (payload.status === 'ok') {
          state.apiBase = base;
          state.mode = 'api';
          elements.modeBadge.textContent = 'API 在线';
          elements.dataBadge.textContent = base;
          if (elements.redisHint) {
            elements.redisHint.style.display = 'none';
          }
          renderStats(await getStats());
          await runSearch();
          return true;
        }
      }
    } catch (e) {
      // continue
    }
  }
  return false;
}

function bindEvents() {
  elements.searchButton.addEventListener('click', runSearch);
  elements.searchInput.addEventListener('keydown', function (event) {
    if (event.key === 'Enter') {
      runSearch();
    }
  });
}

async function init() {
  bindEvents();

  try {
    await loadDemoData();
  } catch (e) {
    elements.modeBadge.textContent = '数据加载失败';
    elements.dataBadge.textContent = e.message;
    if (elements.redisHint) elements.redisHint.style.display = 'none';
    return;
  }

  renderStats(state.demoData.stats);
  await runSearch();

  var apiFound = await tryDetectApi();
  if (!apiFound) {
    elements.modeBadge.textContent = '静态 Demo';
    elements.dataBadge.textContent = './data/demo_samples.json';
    if (elements.redisHint) {
      elements.redisHint.style.display = 'block';
    }
  }
}

init().catch(function (error) {
  console.error(error);
  elements.modeBadge.textContent = '加载失败';
  elements.dataBadge.textContent = error.message;
});
