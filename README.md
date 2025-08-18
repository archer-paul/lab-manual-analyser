# ManualMiner

**[Version française du README](README_FR.md)**

An automated analysis system for medical device manuals using Google Cloud Document AI and Gemini AI. ManualMiner extracts procedures, maintenance protocols, technical specifications, and safety guidelines from PDF manuals to generate comprehensive synthesis documents.

## Features

- **Automated PDF Processing**: Handles encrypted PDFs and documents up to several hundred pages
- **Intelligent Text Extraction**: Uses Google Cloud Document AI with OCR capabilities
- **AI-Powered Analysis**: Leverages Gemini AI to identify and structure information
- **Comprehensive Synthesis**: Generates professional PDF summaries and detailed JSON reports
- **Organized Output**: Automatically organizes results in structured directories

## Extracted Information

The system identifies and extracts:

- **General Information**: Instrument name, manufacturer, model, applications
- **Analysis Procedures**: Step-by-step protocols with materials and precautions
- **Preventive Maintenance**: Schedules, procedures, and verification points
- **Technical Specifications**: Performance parameters and environmental requirements
- **Safety Guidelines**: Risk assessments and protective measures
- **Calibration Procedures**: Quality control and standard requirements

## Prerequisites

### Google Cloud Platform
1. **Google Cloud Project** with billing enabled
2. **Document AI API** activated
3. **Document AI OCR Processor** created
4. **Service Account** with Document AI API User role
5. **Service Account JSON key** downloaded

### Gemini AI
- **Gemini API key** from Google AI Studio

### Python Dependencies
- Python 3.8 or higher
- Dependencies listed in `requirements.txt`

## Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/lab-manual-analyzer.git
cd lab-manual-analyzer
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Run setup script**
```bash
python setup.py
```

4. **Configure APIs**
   - Place your service account JSON file in `credentials/`
   - Update `config.json` with your project details

5. **Test configuration**
```bash
python test_config.py
```

## Quick Start

1. **Place PDF manuals** in the `manuels/` directory
2. **Run analysis**:
```bash
python lab_manual_analyzer_organized.py manuels/your_manual.pdf
```
3. **Find results** in `manuels/syntheses/`

## Configuration

Edit `config.json` with your Google Cloud and Gemini settings:

```json
{
  "google_cloud": {
    "project_id": "your-project-id",
    "location": "us",
    "processor_id": "your-processor-id",
    "credentials_path": "credentials/service-account.json"
  },
  "gemini": {
    "api_key": "your-gemini-api-key",
    "model": "gemini-1.5-pro"
  },
  "analysis": {
    "max_pages_per_chunk": 15,
    "delay_between_requests": 2
  }
}
```

## Output Structure

```
manuels/
├── your_manual.pdf              # Source PDF
└── syntheses/
    ├── your_manual_SYNTHESE.pdf     # Professional summary
    └── your_manual_ANALYSE_COMPLETE.json  # Detailed analysis
```

## Advanced Usage

### Batch Processing
```bash
# Process all PDFs in directory
for pdf in manuels/*.pdf; do
    python lab_manual_analyzer_organized.py "$pdf"
done
```

### Custom Configuration
```bash
python lab_manual_analyzer_organized.py manual.pdf --config custom_config.json
```

## Technical Details

### Document Processing Pipeline
1. **PDF Preparation**: Automatic decryption if password-protected
2. **Intelligent Chunking**: Splits large documents (>15 pages) for API limits
3. **OCR Extraction**: Uses Document AI for robust text extraction
4. **AI Analysis**: Gemini AI identifies and structures information
5. **Synthesis Generation**: Creates professional PDF and JSON outputs

### API Limits and Costs
- **Document AI**: 15 pages per request, ~$1 per 1000 pages
- **Gemini**: ~$7 per 1M tokens, typical manual costs $1-2
- **Processing Time**: 5-20 minutes per manual depending on size

## Troubleshooting

### Common Issues

**"PAGE_LIMIT_EXCEEDED" Error**
- Ensure Document AI processor is properly configured
- Check that chunks are ≤15 pages

**JSON Parsing Errors**
- Increase delay between requests in config
- Check Gemini API quotas

**No Text Extracted**
- Verify PDF is not corrupted or image-only
- Check service account permissions

### Support Files
- Check `lab_analysis.log` for detailed logs
- Review `test_config.py` output for configuration issues

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with appropriate tests
4. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Citation

If you use this tool in academic research, please cite:

```
Lab Manual Analyzer: Automated Analysis of Laboratory Instrument Documentation
[Your details here]
```

## Acknowledgments

- Google Cloud Document AI for OCR capabilities
- Google Gemini AI for intelligent text analysis
- ReportLab for PDF generation