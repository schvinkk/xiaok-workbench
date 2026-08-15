# 小K万能工作台 - 个人竞争力分析功能设计方案

## 1. 功能概述

个人竞争力分析功能旨在帮助用户全面评估自身在职场中的竞争力水平，通过多维度数据分析、可视化和对比，为用户提供清晰的自我认知和改进方向。

## 2. 分析维度设计

### 2.1 技能水平分析
**评估维度：**
- 技术技能熟练度（编程语言、工具、框架等）
- 软技能（沟通、协作、领导力等）
- 专业认证持有情况
- 项目经验丰富程度
- 学习能力与成长速度

**评估方法：**
- 自我评分（1-10分制）
- 技能证书验证
- 项目成果量化
- 同行评价收集

### 2.2 经验匹配分析
**评估维度：**
- 工作年限与岗位匹配度
- 项目复杂度与规模
- 行业经验深度
- 管理经验（如适用）
- 跨部门/跨领域经验

**评估方法：**
- 职业履历分析
- 项目难度评级
- 责任级别评估
- 成果影响力评估

### 2.3 学历背景分析
**评估维度：**
- 学历层次（本科、硕士、博士等）
- 专业相关性
- 毕业院校声誉
- 持续教育情况
- 国际化教育背景

**评估方法：**
- 学历信息验证
- 专业与岗位匹配度计算
- 继续教育学分统计
- 国际交流经历评估

### 2.4 行业趋势分析
**评估维度：**
- 技术发展趋势
- 市场需求变化
- 薪资水平趋势
- 就业机会预测
- 新兴技能需求

**评估方法：**
- 行业报告分析
- 招聘数据挖掘
- 技术热度追踪
- 薪资调研数据

## 3. 数据可视化设计

### 3.1 雷达图展示
**用途：** 直观展示多维度能力分布
**实现：**
- 使用Chart.js或ECharts绘制五维雷达图
- 每个维度显示当前值和目标值
- 支持交互式查看详细数据
- 颜色编码：绿色(优秀)、黄色(一般)、红色(需提升)

**数据结构：**
```javascript
{
  skills: { name: '技能水平', value: 8, target: 9 },
  experience: { name: '经验匹配', value: 7, target: 8 },
  education: { name: '学历背景', value: 6, target: 7 },
  industry: { name: '行业趋势', value: 8, target: 9 }
}
```

### 3.2 趋势图展示
**用途：** 展示竞争力随时间的变化趋势
**实现：**
- 时间轴折线图展示6-12个月的变化
- 支持多维度趋势对比
- 关键节点标记（如获得认证、完成项目等）
- 预测趋势线（基于历史数据）

### 3.3 对比分析图
**用途：** 与基准进行对比分析
**实现：**
- 柱状图展示与地区平均水平的对比
- 堆叠图展示与行业标杆的差距
- 支持多维度同时对比
- 差距百分比标注

## 4. 对比基准设计

### 4.1 同地区同岗位平均水平
**数据来源：**
- 政府就业统计数据
- 招聘平台薪资数据
- 行业调研报告
- 高校就业质量报告

**对比维度：**
- 薪资水平对比
- 技能要求对比
- 工作经验要求对比
- 学历要求对比

### 4.2 行业标杆对比
**数据来源：**
- 行业领军企业招聘要求
- 专业认证标准
- 行业最佳实践
- 国际标准对比

**对比维度：**
- 核心技能要求对比
- 经验级别对比
- 专业资质对比
- 综合能力对比

### 4.3 自我历史对比
**功能特点：**
- 历史数据回溯（6个月-2年）
- 进步速度评估
- 阶段性目标达成情况
- 成长轨迹分析

## 5. 改进建议系统

### 5.1 基于数据的智能建议
**建议类型：**
- 技能提升建议
- 学习路径推荐
- 证书获取建议
- 项目经验积累建议
- 行业趋势适应建议

**算法逻辑：**
```javascript
function generateImprovementSuggestions(currentData, benchmarks) {
  const suggestions = [];
  
  // 分析差距
  const gaps = analyzeGaps(currentData, benchmarks);
  
  // 生成针对性建议
  gaps.forEach(gap => {
    if (gap.type === 'skill') {
      suggestions.push({
        category: '技能提升',
        priority: gap.severity,
        action: getSkillImprovementAction(gap.skill),
        timeline: getRecommendedTimeline(gap.skill),
        resources: getLearningResources(gap.skill)
      });
    }
    // 其他类型建议...
  });
  
  return sortSuggestionsByPriority(suggestions);
}
```

### 5.2 个性化学习路径
**路径设计：**
- 短期目标（1-3个月）
- 中期目标（3-6个月）
- 长期目标（6-12个月）
- 里程碑设置

**资源推荐：**
- 在线课程
- 认证考试
- 实践项目
- 社区参与

### 5.3 进度跟踪系统
**跟踪功能：**
- 目标完成度监控
- 学习时长统计
- 技能提升记录
- 成果展示平台

## 6. 单文件版实现方案

### 6.1 技术架构
**前端技术栈：**
- HTML5 + CSS3 + JavaScript (ES6+)
- Chart.js/ECharts 用于数据可视化
- LocalStorage 用于数据存储
- 响应式设计

**文件结构：**
```
competitiveness-analyzer.html
├── css/
│   ├── style.css          # 主样式文件
│   └── charts.css         # 图表样式
├── js/
│   ├── app.js             # 主应用逻辑
│   ├── charts.js          # 图表绘制逻辑
│   ├── dataProcessor.js   # 数据处理逻辑
│   └── suggestions.js     # 建议生成逻辑
└── data/
    ├── benchmarks.json    # 基准数据
    └── templates.json     # 模板数据
```

### 6.2 核心功能模块

#### 6.2.1 数据采集模块
```javascript
// dataCollector.js
class DataCollector {
  constructor() {
    this.userData = this.loadUserData();
    this.benchmarks = this.loadBenchmarks();
  }
  
  // 收集用户技能数据
  collectSkillData() {
    const skills = this.promptForSkills();
    this.calculateSkillScores(skills);
    return this.userData.skills;
  }
  
  // 收集经验数据
  collectExperienceData() {
    const experience = this.promptForExperience();
    this.calculateExperienceScore(experience);
    return this.userData.experience;
  }
  
  // 收集学历数据
  collectEducationData() {
    const education = this.promptForEducation();
    this.calculateEducationScore(education);
    return this.userData.education;
  }
  
  // 收集行业数据
  collectIndustryData() {
    const industry = this.promptForIndustry();
    this.calculateIndustryScore(industry);
    return this.userData.industry;
  }
}
```

#### 6.2.2 数据分析模块
```javascript
// dataProcessor.js
class DataProcessor {
  constructor(userData, benchmarks) {
    this.userData = userData;
    this.benchmarks = benchmarks;
  }
  
  // 计算综合竞争力得分
  calculateOverallScore() {
    const weights = { skills: 0.3, experience: 0.3, education: 0.2, industry: 0.2 };
    let totalScore = 0;
    
    Object.keys(weights).forEach(key => {
      totalScore += this.userData[key].score * weights[key];
    });
    
    return Math.round(totalScore * 100) / 100;
  }
  
  // 分析差距
  analyzeGaps() {
    const gaps = {};
    
    Object.keys(this.userData).forEach(key => {
      const userScore = this.userData[key].score;
      const benchmarkScore = this.benchmarks[key].average;
      const gap = benchmarkScore - userScore;
      
      gaps[key] = {
        current: userScore,
        target: benchmarkScore,
        gap: gap,
        percentage: Math.round((gap / benchmarkScore) * 100)
      };
    });
    
    return gaps;
  }
  
  // 生成趋势数据
  generateTrendData(historicalData) {
    // 基于历史数据生成趋势分析
    return this.calculateTrend(historicalData);
  }
}
```

#### 6.2.3 可视化模块
```javascript
// charts.js
class ChartManager {
  constructor() {
    this.charts = {};
  }
  
  // 绘制雷达图
  drawRadarChart(data, containerId) {
    const ctx = document.getElementById(containerId).getContext('2d');
    
    new Chart(ctx, {
      type: 'radar',
      data: {
        labels: Object.keys(data),
        datasets: [{
          label: '当前水平',
          data: Object.values(data).map(d => d.value),
          backgroundColor: 'rgba(54, 162, 235, 0.2)',
          borderColor: 'rgba(54, 162, 235, 1)',
          borderWidth: 2
        }, {
          label: '目标水平',
          data: Object.values(data).map(d => d.target),
          backgroundColor: 'rgba(255, 99, 132, 0.2)',
          borderColor: 'rgba(255, 99, 132, 1)',
          borderWidth: 2
        }]
      },
      options: {
        scales: {
          r: {
            beginAtZero: true,
            max: 10
          }
        }
      }
    });
  }
  
  // 绘制对比柱状图
  drawComparisonChart(userData, benchmarkData, containerId) {
    const ctx = document.getElementById(containerId).getContext('2d');
    
    new Chart(ctx, {
      type: 'bar',
      data: {
        labels: Object.keys(userData),
        datasets: [{
          label: '个人水平',
          data: Object.values(userData).map(d => d.score),
          backgroundColor: 'rgba(54, 162, 235, 0.6)'
        }, {
          label: '平均水平',
          data: Object.values(benchmarkData).map(d => d.average),
          backgroundColor: 'rgba(255, 99, 132, 0.6)'
        }]
      },
      options: {
        responsive: true,
        scales: {
          y: {
            beginAtZero: true,
            max: 10
          }
        }
      }
    });
  }
  
  // 绘制趋势图
  drawTrendChart(trendData, containerId) {
    const ctx = document.getElementById(containerId).getContext('2d');
    
    new Chart(ctx, {
      type: 'line',
      data: {
        labels: trendData.labels,
        datasets: [{
          label: '竞争力得分',
          data: trendData.scores,
          borderColor: 'rgba(75, 192, 192, 1)',
          backgroundColor: 'rgba(75, 192, 192, 0.2)',
          tension: 0.1
        }]
      },
      options: {
        responsive: true,
        scales: {
          y: {
            beginAtZero: true,
            max: 10
          }
        }
      }
    });
  }
}
```

#### 6.2.4 建议生成模块
```javascript
// suggestions.js
class SuggestionEngine {
  constructor(userData, benchmarks) {
    this.userData = userData;
    this.benchmarks = benchmarks;
    this.suggestionTemplates = this.loadSuggestionTemplates();
  }
  
  // 生成改进建议
  generateSuggestions() {
    const suggestions = [];
    const gaps = this.analyzeGaps();
    
    Object.keys(gaps).forEach(key => {
      const gap = gaps[key];
      if (gap.gap > 1) { // 差距超过1分才生成建议
        const categorySuggestions = this.generateCategorySuggestions(key, gap);
        suggestions.push(...categorySuggestions);
      }
    });
    
    return this.rankSuggestions(suggestions);
  }
  
  // 生成分类建议
  generateCategorySuggestions(category, gap) {
    const templates = this.suggestionTemplates[category];
    const suggestions = [];
    
    templates.forEach(template => {
      if (this.isApplicable(template, gap)) {
        const suggestion = {
          id: this.generateId(),
          category: category,
          title: template.title,
          description: this.fillTemplate(template.description, gap),
          priority: this.calculatePriority(template, gap),
          timeline: template.timeline,
          resources: template.resources,
          actionItems: template.actionItems
        };
        suggestions.push(suggestion);
      }
    });
    
    return suggestions;
  }
  
  // 排序建议
  rankSuggestions(suggestions) {
    return suggestions.sort((a, b) => b.priority - a.priority);
  }
}
```

### 6.3 主应用逻辑
```javascript
// app.js
class CompetitivenessAnalyzer {
  constructor() {
    this.dataCollector = new DataCollector();
    this.dataProcessor = null;
    this.chartManager = new ChartManager();
    this.suggestionEngine = null;
    this.currentView = 'input';
  }
  
  // 初始化应用
  init() {
    this.setupEventListeners();
    this.showInputView();
  }
  
  // 显示数据输入界面
  showInputView() {
    this.currentView = 'input';
    document.getElementById('input-section').style.display = 'block';
    document.getElementById('analysis-section').style.display = 'none';
  }
  
  // 显示分析结果界面
  showAnalysisView() {
    this.currentView = 'analysis';
    document.getElementById('input-section').style.display = 'none';
    document.getElementById('analysis-section').style.display = 'block';
    
    // 收集数据
    const userData = this.collectUserData();
    
    // 处理数据
    this.dataProcessor = new DataProcessor(userData, this.dataCollector.benchmarks);
    
    // 显示图表
    this.displayCharts();
    
    // 生成建议
    this.displaySuggestions();
  }
  
  // 收集用户数据
  collectUserData() {
    return {
      skills: this.dataCollector.collectSkillData(),
      experience: this.dataCollector.collectExperienceData(),
      education: this.dataCollector.collectEducationData(),
      industry: this.dataCollector.collectIndustryData()
    };
  }
  
  // 显示图表
  displayCharts() {
    const userData = this.dataProcessor.userData;
    const gaps = this.dataProcessor.analyzeGaps();
    
    // 雷达图
    this.chartManager.drawRadarChart(gaps, 'radar-chart');
    
    // 对比图
    this.chartManager.drawComparisonChart(
      userData, 
      this.dataCollector.benchmarks, 
      'comparison-chart'
    );
    
    // 趋势图
    const trendData = this.dataProcessor.generateTrendData(this.loadHistoricalData());
    this.chartManager.drawTrendChart(trendData, 'trend-chart');
  }
  
  // 显示建议
  displaySuggestions() {
    this.suggestionEngine = new SuggestionEngine(
      this.dataProcessor.userData, 
      this.dataCollector.benchmarks
    );
    
    const suggestions = this.suggestionEngine.generateSuggestions();
    this.renderSuggestions(suggestions);
  }
}
```

### 6.4 数据存储方案

#### 6.4.1 LocalStorage结构
```javascript
// 数据存储键值
const STORAGE_KEYS = {
  USER_DATA: 'competitiveness_user_data',
  HISTORICAL_DATA: 'competitiveness_historical_data',
  SETTINGS: 'competitiveness_settings'
};

// 用户数据结构
const userDataStructure = {
  id: 'user_' + Date.now(),
  name: '',
  skills: {
    technical: [],
    soft: [],
    certifications: []
  },
  experience: {
    totalYears: 0,
    projects: [],
    management: false,
    industries: []
  },
  education: {
    degree: '',
    major: '',
    institution: '',
    year: ''
  },
  industry: {
    current: '',
    target: '',
    trends: []
  },
  assessmentDate: new Date().toISOString(),
  scores: {
    skills: 0,
    experience: 0,
    education: 0,
    industry: 0,
    overall: 0
  }
};
```

#### 6.4.2 数据持久化
```javascript
// storageManager.js
class StorageManager {
  constructor() {
    this.prefix = 'competitiveness_';
  }
  
  // 保存用户数据
  saveUserData(data) {
    localStorage.setItem(this.prefix + 'user_data', JSON.stringify(data));
  }
  
  // 加载用户数据
  loadUserData() {
    const data = localStorage.getItem(this.prefix + 'user_data');
    return data ? JSON.parse(data) : null;
  }
  
  // 保存历史数据
  saveHistoricalData(data) {
    const existing = this.loadHistoricalData();
    const updated = [...existing, data];
    localStorage.setItem(this.prefix + 'historical_data', JSON.stringify(updated));
  }
  
  // 加载历史数据
  loadHistoricalData() {
    const data = localStorage.getItem(this.prefix + 'historical_data');
    return data ? JSON.parse(data) : [];
  }
  
  // 清除所有数据
  clearAllData() {
    Object.keys(localStorage).forEach(key => {
      if (key.startsWith(this.prefix)) {
        localStorage.removeItem(key);
      }
    });
  }
}
```

### 6.5 界面设计

#### 6.5.1 HTML结构
```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>个人竞争力分析 - 小K万能工作台</title>
    <link rel="stylesheet" href="css/style.css">
    <link rel="stylesheet" href="css/charts.css">
</head>
<body>
    <div class="container">
        <header>
            <h1>个人竞争力分析</h1>
            <p>全面评估您的职场竞争力，制定提升计划</p>
        </header>
        
        <!-- 数据输入部分 -->
        <section id="input-section">
            <div class="step-container">
                <div class="step active" data-step="1">1</div>
                <div class="step" data-step="2">2</div>
                <div class="step" data-step="3">3</div>
                <div class="step" data-step="4">4</div>
            </div>
            
            <form id="competitiveness-form">
                <div class="form-step" data-step="1">
                    <h2>技能水平评估</h2>
                    <!-- 技能评估表单内容 -->
                </div>
                
                <div class="form-step" data-step="2">
                    <h2>经验匹配评估</h2>
                    <!-- 经验评估表单内容 -->
                </div>
                
                <div class="form-step" data-step="3">
                    <h2>学历背景评估</h2>
                    <!-- 学历评估表单内容 -->
                </div>
                
                <div class="form-step" data-step="4">
                    <h2>行业趋势分析</h2>
                    <!-- 行业分析表单内容 -->
                </div>
                
                <div class="form-actions">
                    <button type="button" id="prev-btn" style="display: none;">上一步</button>
                    <button type="button" id="next-btn">下一步</button>
                    <button type="submit" id="submit-btn" style="display: none;">生成分析报告</button>
                </div>
            </form>
        </section>
        
        <!-- 分析结果部分 -->
        <section id="analysis-section" style="display: none;">
            <div class="results-container">
                <div class="summary-card">
                    <h2>竞争力总览</h2>
                    <div class="overall-score">
                        <span class="score-value" id="overall-score">0</span>
                        <span class="score-label">综合得分</span>
                    </div>
                    <div class="score-details">
                        <div class="score-item">
                            <span class="score-label">技能水平</span>
                            <span class="score-value" id="skills-score">0</span>
                        </div>
                        <div class="score-item">
                            <span class="score-label">经验匹配</span>
                            <span class="score-value" id="experience-score">0</span>
                        </div>
                        <div class="score-item">
                            <span class="score-label">学历背景</span>
                            <span class="score-value" id="education-score">0</span>
                        </div>
                        <div class="score-item">
                            <span class="score-label">行业趋势</span>
                            <span class="score-value" id="industry-score">0</span>
                        </div>
                    </div>
                </div>
                
                <div class="charts-container">
                    <div class="chart-card">
                        <h3>能力雷达图</h3>
                        <canvas id="radar-chart"></canvas>
                    </div>
                    
                    <div class="chart-card">
                        <h3>对比分析</h3>
                        <canvas id="comparison-chart"></canvas>
                    </div>
                    
                    <div class="chart-card">
                        <h3>趋势分析</h3>
                        <canvas id="trend-chart"></canvas>
                    </div>
                </div>
                
                <div class="suggestions-container">
                    <h2>改进建议</h2>
                    <div id="suggestions-list"></div>
                </div>
                
                <div class="actions-container">
                    <button id="save-report-btn">保存报告</button>
                    <button id="new-analysis-btn">重新分析</button>
                    <button id="export-data-btn">导出数据</button>
                </div>
            </div>
        </section>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="js/dataCollector.js"></script>
    <script src="js/dataProcessor.js"></script>
    <script src="js/charts.js"></script>
    <script src="js/suggestions.js"></script>
    <script src="js/storageManager.js"></script>
    <script src="js/app.js"></script>
</body>
</html>
```

#### 6.5.2 CSS样式
```css
/* style.css */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Microsoft YaHei', Arial, sans-serif;
    line-height: 1.6;
    color: #333;
    background-color: #f5f7fa;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
}

header {
    text-align: center;
    margin-bottom: 30px;
    padding: 20px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border-radius: 10px;
}

header h1 {
    font-size: 2.5em;
    margin-bottom: 10px;
}

.step-container {
    display: flex;
    justify-content: center;
    margin-bottom: 30px;
}

.step {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    background-color: #e0e0e0;
    color: #666;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 10px;
    font-weight: bold;
    transition: all 0.3s ease;
}

.step.active {
    background-color: #667eea;
    color: white;
}

.step.completed {
    background-color: #4caf50;
    color: white;
}

.form-step {
    display: none;
    background: white;
    padding: 30px;
    border-radius: 10px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    margin-bottom: 20px;
}

.form-step.active {
    display: block;
}

.form-step h2 {
    color: #667eea;
    margin-bottom: 20px;
}

.form-group {
    margin-bottom: 20px;
}

.form-group label {
    display: block;
    margin-bottom: 5px;
    font-weight: bold;
}

.form-group input,
.form-group select,
.form-group textarea {
    width: 100%;
    padding: 10px;
    border: 1px solid #ddd;
    border-radius: 5px;
    font-size: 16px;
}

.form-group input:focus,
.form-group select:focus,
.form-group textarea:focus {
    outline: none;
    border-color: #667eea;
}

.skill-item {
    display: flex;
    align-items: center;
    margin-bottom: 15px;
}

.skill-item label {
    width: 150px;
    margin-right: 10px;
}

.skill-item input[type="range"] {
    flex: 1;
    margin-right: 10px;
}

.skill-value {
    width: 40px;
    text-align: center;
    font-weight: bold;
}

.form-actions {
    display: flex;
    justify-content: space-between;
    margin-top: 30px;
}

.form-actions button {
    padding: 12px 30px;
    border: none;
    border-radius: 5px;
    font-size: 16px;
    cursor: pointer;
    transition: all 0.3s ease;
}

.form-actions button[type="button"] {
    background-color: #e0e0e0;
    color: #666;
}

.form-actions button[type="button"]:hover {
    background-color: #d0d0d0;
}

.form-actions button[type="submit"] {
    background-color: #667eea;
    color: white;
}

.form-actions button[type="submit"]:hover {
    background-color: #5a67d8;
}

.results-container {
    display: grid;
    gap: 20px;
}

.summary-card {
    background: white;
    padding: 30px;
    border-radius: 10px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    text-align: center;
}

.overall-score {
    margin: 20px 0;
}

.score-value {
    font-size: 3em;
    font-weight: bold;
    color: #667eea;
}

.score-label {
    display: block;
    margin-top: 5px;
    color: #666;
}

.score-details {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 20px;
    margin-top: 30px;
}

.score-item {
    text-align: center;
}

.charts-container {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
    gap: 20px;
    margin-bottom: 30px;
}

.chart-card {
    background: white;
    padding: 20px;
    border-radius: 10px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

.chart-card h3 {
    margin-bottom: 15px;
    color: #667eea;
    text-align: center;
}

.chart-card canvas {
    max-height: 300px;
}

.suggestions-container {
    background: white;
    padding: 30px;
    border-radius: 10px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

.suggestions-container h2 {
    color: #667eea;
    margin-bottom: 20px;
}

.suggestion-item {
    background: #f8f9fa;
    padding: 20px;
    border-radius: 8px;
    margin-bottom: 15px;
    border-left: 4px solid #667eea;
}

.suggestion-item h4 {
    color: #333;
    margin-bottom: 10px;
}

.suggestion-item p {
    color: #666;
    margin-bottom: 10px;
}

.suggestion-priority {
    display: inline-block;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 12px;
    font-weight: bold;
    margin-bottom: 10px;
}

.priority-high {
    background-color: #ffebee;
    color: #c62828;
}

.priority-medium {
    background-color: #fff3e0;
    color: #ef6c00;
}

.priority-low {
    background-color: #e8f5e9;
    color: #2e7d32;
}

.suggestion-timeline {
    color: #667eea;
    font-weight: bold;
    margin-bottom: 10px;
}

.suggestion-resources {
    background: #e3f2fd;
    padding: 10px;
    border-radius: 5px;
    margin-bottom: 10px;
}

.suggestion-resources h5 {
    color: #1976d2;
    margin-bottom: 5px;
}

.suggestion-resources ul {
    margin-left: 20px;
}

.suggestion-actions {
    list-style: none;
    margin-top: 10px;
}

.suggestion-actions li {
    margin-bottom: 5px;
    position: relative;
    padding-left: 20px;
}

.suggestion-actions li:before {
    content: "▸";
    position: absolute;
    left: 0;
    color: #667eea;
}

.actions-container {
    display: flex;
    justify-content: center;
    gap: 15px;
    margin-top: 30px;
}

.actions-container button {
    padding: 12px 25px;
    border: none;
    border-radius: 5px;
    font-size: 16px;
    cursor: pointer;
    transition: all 0.3s ease;
}

#save-report-btn {
    background-color: #4caf50;
    color: white;
}

#save-report-btn:hover {
    background-color: #45a049;
}

#new-analysis-btn {
    background-color: #ff9800;
    color: white;
}

#new-analysis-btn:hover {
    background-color: #f57c00;
}

#export-data-btn {
    background-color: #2196f3;
    color: white;
}

#export-data-btn:hover {
    background-color: #1976d2;
}

@media (max-width: 768px) {
    .score-details {
        grid-template-columns: repeat(2, 1fr);
    }
    
    .charts-container {
        grid-template-columns: 1fr;
    }
    
    .form-actions {
        flex-direction: column;
        gap: 10px;
    }
    
    .actions-container {
        flex-direction: column;
    }
}
```

## 7. 功能特色

### 7.1 智能评估系统
- 多维度综合评分
- 动态权重调整
- 个性化评估标准

### 7.2 可视化展示
- 交互式图表
- 实时数据更新
- 响应式设计

### 7.3 智能建议引擎
- 基于数据的建议生成
- 优先级排序
- 行动计划制定

### 7.4 数据追踪
- 历史数据记录
- 进度跟踪
- 成长趋势分析

## 8. 使用流程

1. **数据输入**：用户填写个人信息、技能、经验等
2. **自动分析**：系统计算各项得分和综合竞争力
3. **可视化展示**：通过图表直观展示分析结果
4. **建议生成**：基于分析结果提供改进建议
5. **目标制定**：用户可以设置改进目标
6. **进度跟踪**：定期更新数据，跟踪改进进度

## 9. 技术优势

- **单文件实现**：易于部署和使用
- **数据本地存储**：保护用户隐私
- **响应式设计**：适配各种设备
- **交互性强**：用户体验友好
- **可扩展性**：便于后续功能扩展

## 10. 后续优化方向

1. **增加更多评估维度**：如人脉资源、品牌影响力等
2. **引入AI分析**：更精准的差距分析和建议生成
3. **社交功能**：与同行对比、经验分享
4. **职业规划整合**：与职业发展路径结合
5. **多语言支持**：国际化扩展

这个设计方案充分考虑了个人竞争力分析的各个方面，从数据采集、分析处理到可视化展示和建议生成，形成了一个完整的解决方案。单文件实现方式确保了功能的便捷性和易用性，适合作为小K万能工作台的一个核心功能模块。