"""
EduPredict Pro - Flask Application
AI Degree Program Planning & Decision Intelligence Tool

No Streamlit. Pure Flask + HTML/CSS/JS.
Hosted on AWS EC2 with Gunicorn.
"""

from flask import Flask, render_template, request, jsonify, send_file
import json
import os
import sys
from io import BytesIO
from datetime import datetime

# Add models to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.forecasting import ForecastInput, EnrollmentForecaster, quick_forecast
from models.roi_calculator import ROIInput, ROICalculator, quick_roi
from models.job_market import JobMarketAnalyzer, quick_ai_report, AIOccupationDatabase

app = Flask(__name__)
app.config['SECRET_KEY'] = 'edupredict-pro-secret-key'

# Initialize models
forecaster = EnrollmentForecaster()
roi_calc = ROICalculator()
job_analyzer = JobMarketAnalyzer()
ai_db = AIOccupationDatabase()

# Configuration
PROGRAMS = ["MS in AI", "BS in AI", "AI in Cybersecurity"]
STUDENT_TYPES = ["International", "Domestic"]
TERMS = ["FA26", "SP27", "FA28"]
SCENARIOS = ["Baseline", "Optimistic", "Conservative"]
STATES = ["CT", "NY", "MA"]


@app.route('/')
def index():
    """Main dashboard page."""
    return render_template('index.html',
                         programs=PROGRAMS,
                         student_types=STUDENT_TYPES,
                         terms=TERMS,
                         scenarios=SCENARIOS,
                         states=STATES)


@app.route('/api/forecast', methods=['POST'])
def api_forecast():
    """API endpoint for enrollment forecast."""
    data = request.get_json()
    
    program = data.get('program', 'MS in AI')
    student_type = data.get('student_type', 'International')
    term = data.get('term', 'FA26')
    scenario = data.get('scenario', 'Baseline')
    state = data.get('state', 'CT')
    
    # Get forecast
    forecast = quick_forecast(program, student_type, term, scenario, state)
    
    # Get ROI
    roi = quick_roi(program, state,
                   forecast.year1_enrollment,
                   forecast.year2_enrollment,
                   forecast.year3_enrollment,
                   student_type)
    
    # Get job market data
    job_signal = job_analyzer.get_signal(state, program)
    ai_exposure = ai_db.get_program_exposure(program)
    
    # Get recommendation
    rec = job_analyzer.get_program_recommendation(state, program)
    
    # Calculate overall recommendation
    if roi.roi_ratio >= 1.5 and forecast.confidence_score >= 0.75:
        recommendation = "STRONG GO"
        rec_class = "strong-go"
    elif roi.roi_ratio >= 1.0 and forecast.confidence_score >= 0.60:
        recommendation = "GO"
        rec_class = "go"
    elif roi.roi_ratio >= 0.7 or forecast.confidence_score >= 0.50:
        recommendation = "CONDITIONAL"
        rec_class = "conditional"
    else:
        recommendation = "RECONSIDER"
        rec_class = "reconsider"
    
    if roi.launch_recommendation == "delay":
        recommendation = "DO NOT LAUNCH"
        rec_class = "do-not-launch"
    
    return jsonify({
        'success': True,
        'forecast': {
            'year1': forecast.year1_enrollment,
            'year2': forecast.year2_enrollment,
            'year3': forecast.year3_enrollment,
            'year1_low': forecast.year1_low,
            'year1_high': forecast.year1_high,
            'pool': forecast.projected_pool,
            'confidence': forecast.confidence_score,
            'confidence_pct': int(forecast.confidence_score * 100),
            'risk_level': forecast.risk_level,
            'recommendation_confidence': forecast.recommendation_confidence,
            'warning_flags': forecast.warning_flags
        },
        'roi': {
            'ratio': roi.roi_ratio,
            'starting_salary': roi.starting_salary,
            'salary_5year': roi.salary_5year,
            'revenue': roi.total_tuition_revenue,
            'costs': roi.program_cost_estimate,
            'payback_years': roi.payback_period_years,
            'break_even': roi.break_even_enrollment,
            'financial_warnings': roi.financial_warnings
        },
        'job_market': {
            'growth_rate': job_signal.job_growth_rate,
            'open_positions': job_signal.open_positions_estimate,
            'demand_level': job_signal.demand_level,
            'demand_score': job_analyzer.get_demand_score(state, program),
            'ai_exposure': ai_exposure.observed_exposure,
            'ai_exposure_pct': int(ai_exposure.observed_exposure * 100),
            'risk_level': ai_exposure.risk_level.value,
            'coverage_gap': ai_exposure.coverage_gap,
            'bls_impact': ai_exposure.bls_growth_projection_2034,
            'young_worker_impact': ai_exposure.young_worker_hiring_impact,
            'key_finding': ai_exposure.key_finding
        },
        'recommendation': {
            'text': recommendation,
            'class': rec_class,
            'demand_score': rec['demand_score'],
            'rationale': rec['rationale'],
            'warnings': rec['warnings'],
            'opportunities': rec['opportunities']
        },
        'inputs': {
            'program': program,
            'student_type': student_type,
            'term': term,
            'scenario': scenario,
            'state': state
        }
    })


@app.route('/api/scenarios', methods=['POST'])
def api_scenarios():
    """Get all scenario comparisons."""
    data = request.get_json()
    
    program = data.get('program', 'MS in AI')
    student_type = data.get('student_type', 'International')
    term = data.get('term', 'FA26')
    state = data.get('state', 'CT')
    
    scenarios_data = []
    for scen in SCENARIOS:
        forecast = quick_forecast(program, student_type, term, scen, state)
        scenarios_data.append({
            'scenario': scen,
            'year1': forecast.year1_enrollment,
            'pool': forecast.projected_pool,
            'confidence': forecast.confidence_score
        })
    
    return jsonify({'scenarios': scenarios_data})


@app.route('/api/states', methods=['POST'])
def api_states():
    """Get state comparison data."""
    data = request.get_json()
    
    program = data.get('program', 'MS in AI')
    student_type = data.get('student_type', 'International')
    scenario = data.get('scenario', 'Baseline')
    term = data.get('term', 'FA26')
    
    states_data = []
    for st in STATES:
        forecast = quick_forecast(program, student_type, term, scenario, st)
        job_signal = job_analyzer.get_signal(st, program)
        states_data.append({
            'state': st,
            'year1': forecast.year1_enrollment,
            'year2': forecast.year2_enrollment,
            'year3': forecast.year3_enrollment,
            'pool': forecast.projected_pool,
            'growth_rate': job_signal.job_growth_rate,
            'demand_score': job_analyzer.get_demand_score(st, program)
        })
    
    return jsonify({'states': states_data})


@app.route('/api/validate')
def api_validate():
    """Validate all 162 combinations."""
    results = []
    passed = 0
    failed = 0
    
    for program in PROGRAMS:
        for student_type in STUDENT_TYPES:
            for term in TERMS:
                for scenario in SCENARIOS:
                    for state in STATES:
                        try:
                            forecast = quick_forecast(program, student_type, term, scenario, state)
                            roi = quick_roi(program, state,
                                          forecast.year1_enrollment,
                                          forecast.year2_enrollment,
                                          forecast.year3_enrollment,
                                          student_type)
                            
                            # Basic sanity checks
                            assert forecast.year1_enrollment >= 0
                            assert forecast.year2_enrollment >= forecast.year1_enrollment * 0.8
                            assert roi.roi_ratio >= 0
                            
                            passed += 1
                        except Exception as e:
                            failed += 1
                            results.append({
                                'combination': f"{program} + {student_type} + {term} + {scenario} + {state}",
                                'error': str(e)
                            })
    
    return jsonify({
        'total': passed + failed,
        'passed': passed,
        'failed': failed,
        'success_rate': passed / (passed + failed) * 100,
        'errors': results[:10]  # First 10 errors only
    })


@app.route('/api/ai-report/<program>')
def api_ai_report(program):
    """Get AI exposure report for a program."""
    report = quick_ai_report(program)
    return jsonify(report)


@app.route('/health')
def health():
    """Health check endpoint for AWS."""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})


if __name__ == '__main__':
    # Development server
    app.run(host='0.0.0.0', port=5000, debug=True)
