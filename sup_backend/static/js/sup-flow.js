/**
 * sup — Alpine.js component for the cascading financial flow.
 *
 * Tier 1: Pure client-side (no server calls). Runway + target number.
 * Tier 2: HTMX saves to server, triggers projection.
 */
function supFlow() {
  return {
    // Flow state
    step: 1,
    tier: 1,
    projecting: false,
    projectionDone: false,
    showWhatIf: false,
    showDetails: false,
    targetPulsing: false,

    // Tier 1 inputs
    purpose: '',
    ventureName: '',
    ventureStage: '',
    familyType: '',
    numKids: 1,
    kidAges: [5],
    numDependents: 1,
    dependentCost: 0,
    monthlySurvival: 0,
    monthlyLifestyle: 0,
    liquidSavings: 0,
    monthlyPassive: 0,
    emergencyMonths: 6,

    // Tier 2 inputs
    wealthLevel: 0,
    incomeLevel: 0,
    expenseLevel: 0,
    semiLiquidAssets: 0,
    growthAssets: 0,
    propertyAssets: 0,
    expectedReturn: 12,
    bigExpenses: [],
    hasSideIncome: null,
    sideIncomeAmount: 0,
    sideIncomeDuration: 12,

    // UI toggles
    showExplain: false,

    // Results
    freeUpYear: null,
    chartInstance: null,

    init() {
      // Watch inputs that affect target number (Tier 1 is all client-side)
      this.$watch('monthlySurvival', () => this.pulseTarget());
      this.$watch('monthlyLifestyle', () => this.pulseTarget());
      this.$watch('liquidSavings', () => this.pulseTarget());
      this.$watch('monthlyPassive', () => this.pulseTarget());
      this.$watch('emergencyMonths', () => this.pulseTarget());
      this.$watch('dependentCost', () => this.pulseTarget());

      // Watch numKids to resize kidAges array
      this.$watch('numKids', (val) => {
        while (this.kidAges.length < val) this.kidAges.push(5);
        while (this.kidAges.length > val) this.kidAges.pop();
      });
    },

    // Computed: does family type include kids?
    get hasKids() {
      return this.familyType === 'Partner + kids';
    },

    // Computed: does family type include dependents?
    get hasDependents() {
      return this.familyType === 'Joint family';
    },

    // Computed: total monthly burn (survival)
    get totalSurvivalBurn() {
      return (this.monthlySurvival || 0) + (this.dependentCost || 0);
    },

    // Computed: total monthly burn (comfort)
    get totalComfortBurn() {
      return this.totalSurvivalBurn + (this.monthlyLifestyle || 0);
    },

    // Computed: emergency fund locked amount
    get emergencyLock() {
      return this.emergencyMonths * this.totalSurvivalBurn;
    },

    // Computed: available cash after emergency lock
    get availableCash() {
      return Math.max(0, (this.liquidSavings || 0) - this.emergencyLock);
    },

    // Computed: austerity runway (months)
    get austerityRunway() {
      const netBurn = this.totalSurvivalBurn - (this.monthlyPassive || 0);
      if (netBurn <= 0) return Infinity;
      return this.availableCash / netBurn;
    },

    // Computed: comfort runway (months)
    get comfortRunway() {
      const netBurn = this.totalComfortBurn - (this.monthlyPassive || 0);
      if (netBurn <= 0) return Infinity;
      return this.availableCash / netBurn;
    },

    // Computed: target number (FI corpus = 25x annual survival)
    get targetNumber() {
      return this.totalSurvivalBurn * 12 * 25;
    },

    // Computed: formatted target for header
    get targetFormatted() {
      if (this.targetNumber <= 0) return '';
      return 'Target: ' + this.formatINR(this.targetNumber);
    },

    // Step progression with cascading logic
    nextStep(from) {
      if (from === 1) {
        // If not startup, skip venture step
        if (this.purpose !== 'My startup') {
          this.step = 3;
        } else {
          this.step = 2;
        }
      } else if (from === 2) {
        this.step = 3;
      } else if (from === 3) {
        // After family type, cascade based on selection
        if (this.hasKids) {
          this.step = 3.5;
        } else if (this.hasDependents) {
          this.step = 3.7;
        } else {
          this.step = 4;
        }
      } else if (from === 3.5) {
        if (this.hasDependents) {
          this.step = 3.7;
        } else {
          this.step = 4;
        }
      } else if (from === 3.7) {
        this.step = 4;
      } else if (from === 4) {
        this.step = 5;
      } else if (from === 5) {
        this.step = 6;
      } else if (from === 6) {
        this.step = 7; // Show Tier 1 results
      } else if (from === 8) {
        this.step = 9;
      } else if (from === 9) {
        this.step = 10;
      }

      // Smooth scroll to bottom after step change
      this.$nextTick(() => {
        window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
      });
    },

    // Enter Tier 2
    enterTier2() {
      this.tier = 2;
      this.step = 8;
      this.$nextTick(() => {
        window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
      });
    },

    addBigExpense() {
      if (this.bigExpenses.length < 3) {
        const currentYear = new Date().getFullYear();
        this.bigExpenses.push({ name: '', amount: 0, year: currentYear + 5 });
      }
    },

    // Pulse animation on target number
    pulseTarget() {
      this.targetPulsing = true;
      setTimeout(() => { this.targetPulsing = false; }, 600);
    },

    // Run full projection (Tier 2 → server)
    async runProjection() {
      this.projecting = true;
      const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value
        || document.cookie.match(/csrftoken=([^;]+)/)?.[1] || '';

      try {
        const payload = {
          // Tier 1 data
          purpose: this.purpose,
          venture_name: this.ventureName,
          venture_stage: this.ventureStage,
          family_type: this.familyType,
          num_kids: this.numKids,
          kid_ages: this.kidAges,
          num_dependents: this.numDependents,
          dependent_cost: this.dependentCost,
          monthly_survival: this.monthlySurvival,
          monthly_lifestyle: this.monthlyLifestyle,
          liquid_savings: this.liquidSavings,
          monthly_passive: this.monthlyPassive,
          emergency_months: this.emergencyMonths,
          // Tier 2 data
          wealth_level: this.wealthLevel,
          income_level: this.incomeLevel,
          expense_level: this.expenseLevel,
          semi_liquid_assets: this.semiLiquidAssets,
          growth_assets: this.growthAssets,
          property_assets: this.propertyAssets,
          expected_return: this.expectedReturn,
          big_expenses: this.bigExpenses.filter(e => e.name && e.amount),
          has_side_income: this.hasSideIncome,
          side_income_amount: this.sideIncomeAmount,
          side_income_duration: this.sideIncomeDuration,
        };

        const resp = await fetch('/api/calculate/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken,
          },
          body: JSON.stringify(payload),
        });

        if (resp.ok) {
          const data = await resp.json();
          this.freeUpYear = data.free_up_year;
          this.projectionDone = true;

          this.$nextTick(() => {
            this.renderChart(data.chart_data);
            window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
          });
        }
      } catch (err) {
        console.error('Projection failed:', err);
      } finally {
        this.projecting = false;
      }
    },

    // Render ECharts cashflow chart
    renderChart(chartData) {
      const container = document.getElementById('cashflow-chart');
      if (!container) return;

      if (this.chartInstance) {
        this.chartInstance.dispose();
      }

      this.chartInstance = echarts.init(container);

      const option = {
        backgroundColor: 'transparent',
        tooltip: {
          trigger: 'axis',
          backgroundColor: '#1e293b',
          borderColor: '#334155',
          textStyle: { color: '#f1f5f9' },
          formatter: (params) => {
            let html = `<strong>${params[0].axisValue}</strong><br>`;
            params.forEach(p => {
              html += `${p.marker} ${p.seriesName}: ${this.formatINR(p.value)}<br>`;
            });
            return html;
          },
        },
        legend: {
          top: 0,
          textStyle: { color: '#94a3b8', fontSize: 11 },
        },
        grid: { left: 60, right: 20, top: 40, bottom: 30 },
        xAxis: {
          type: 'category',
          data: chartData.years,
          axisLabel: { color: '#94a3b8' },
          axisLine: { lineStyle: { color: '#334155' } },
        },
        yAxis: {
          type: 'value',
          axisLabel: {
            color: '#94a3b8',
            formatter: (val) => this.formatINR(val),
          },
          splitLine: { lineStyle: { color: '#1e293b' } },
        },
        series: [
          {
            name: 'Needs',
            type: 'bar',
            stack: 'expenses',
            data: chartData.needs,
            itemStyle: { color: '#ef4444' },
            barWidth: '60%',
          },
          {
            name: 'Wants',
            type: 'bar',
            stack: 'expenses',
            data: chartData.wants,
            itemStyle: { color: '#f59e0b' },
          },
          {
            name: 'Income',
            type: 'line',
            data: chartData.incomes,
            lineStyle: { color: '#10b981', width: 2 },
            itemStyle: { color: '#10b981' },
            areaStyle: { color: 'rgba(16, 185, 129, 0.1)' },
          },
          {
            name: 'Assets',
            type: 'line',
            data: chartData.assets,
            lineStyle: { color: '#6366f1', width: 2, type: 'dashed' },
            itemStyle: { color: '#6366f1' },
          },
        ],
      };

      // Mark Free Up year
      if (this.freeUpYear) {
        const yearIdx = chartData.years.indexOf(this.freeUpYear);
        if (yearIdx >= 0) {
          option.series.push({
            name: 'Free Up',
            type: 'line',
            markLine: {
              data: [{ xAxis: yearIdx }],
              label: {
                formatter: '★ Free Up',
                color: '#10b981',
                fontSize: 12,
              },
              lineStyle: { color: '#10b981', type: 'solid', width: 2 },
            },
            data: [],
          });
        }
      }

      this.chartInstance.setOption(option);

      // Responsive resize
      window.addEventListener('resize', () => {
        this.chartInstance?.resize();
      });
    },

    // --- Currency input helpers ---

    // Parse a comma-separated string → number (strips everything except digits)
    parseCommas(str) {
      if (!str) return 0;
      return parseInt(String(str).replace(/[^0-9]/g, ''), 10) || 0;
    },

    // Format number with Indian comma separators (12,34,567)
    formatCommas(num) {
      if (!num) return '';
      const n = Math.round(Number(num));
      if (isNaN(n) || n === 0) return '';
      return n.toLocaleString('en-IN');
    },

    // Short Indian abbreviation without ₹ prefix (for badge display)
    shortINR(num) {
      if (!num || isNaN(num) || num === 0) return '';
      num = Math.round(Number(num));
      if (num >= 10000000) {
        return (num / 10000000).toFixed(1).replace(/\.0$/, '') + ' Cr';
      } else if (num >= 100000) {
        return (num / 100000).toFixed(1).replace(/\.0$/, '') + ' L';
      } else if (num >= 1000) {
        return (num / 1000).toFixed(0) + 'K';
      }
      return String(num);
    },

    // Set a currency field from a formatted input event.
    // Preserves cursor position after reformatting.
    setCurrency(field, event) {
      const el = event.target;
      const raw = el.value;
      const num = this.parseCommas(raw);
      this[field] = num;

      // Reformat the input — preserve cursor relative to end
      const distFromEnd = raw.length - (el.selectionStart || raw.length);
      const formatted = this.formatCommas(num);
      el.value = formatted;
      const newPos = Math.max(0, formatted.length - distFromEnd);
      el.setSelectionRange(newPos, newPos);
    },

    // Set a nested currency field (e.g. bigExpenses[i].amount)
    setCurrencyNested(obj, key, event) {
      const num = this.parseCommas(event.target.value);
      obj[key] = num;
      const el = event.target;
      const raw = el.value;
      const distFromEnd = raw.length - (el.selectionStart || raw.length);
      const formatted = this.formatCommas(num);
      el.value = formatted;
      const newPos = Math.max(0, formatted.length - distFromEnd);
      el.setSelectionRange(newPos, newPos);
    },

    // Format number as Indian currency (₹ with L/Cr)
    formatINR(num) {
      if (num === null || num === undefined || isNaN(num)) return '₹0';
      num = Math.round(num);
      if (num >= 10000000) {
        return '₹' + (num / 10000000).toFixed(1) + ' Cr';
      } else if (num >= 100000) {
        return '₹' + (num / 100000).toFixed(1) + ' L';
      } else if (num >= 1000) {
        return '₹' + (num / 1000).toFixed(0) + 'K';
      }
      return '₹' + num.toLocaleString('en-IN');
    },
  };
}
