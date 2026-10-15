import os
import re
import time
import warnings
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from xml.sax.saxutils import escape

warnings.filterwarnings("ignore", category=FutureWarning)

log_file = 'raw_patch_log.tmp'
pdf_file = 'ansible-roles/os_patching/reports/patch_report.pdf'

if not os.path.exists(log_file):
    print("Error: Missing log dataset.")
    exit(1)

with open(log_file, 'r') as f:
    content = f.read()

match = re.search(r'REPORT_DATA_START(.*?)REPORT_DATA_END', content, re.DOTALL)
if not match:
    print("Warning: Log metadata stream block tokens missing from console output. Creating basic failure page template.")
    os.makedirs(os.path.dirname(pdf_file), exist_ok=True)
    doc = SimpleDocTemplate(pdf_file, pagesize=landscape(letter), rightMargin=30, leftMargin=30, topMargin=35, bottomMargin=35)
    story, styles = [], getSampleStyleSheet()
    err_title = ParagraphStyle('ErrTitle', parent=styles['Heading1'], fontSize=20, textColor=colors.HexColor('#E53E3E'))
    err_body = ParagraphStyle('ErrBody', parent=styles['Normal'], fontSize=10, leading=14)
    story.append(Paragraph('ENTERPRISE LINUX PATCHING REPORT - EXECUTION CRASH', err_title))
    story.append(Spacer(1, 10))
    story.append(Paragraph(f"<b>Generated on:</b> {time.strftime('%Y-%m-%d %H:%M:%S UTC')}", err_body))
    story.append(Spacer(1, 15))
    story.append(Paragraph("<b>CRITICAL PLAYBOOK EXECUTION FAILURE DETECTED:</b><br/>The targeted node environment crashed or hit network resolution lockout barriers during the infrastructure precheck phase. Check your live Jenkins console logs to diagnose the network mirror timeouts.", err_body))
    doc.build(story)
    exit(0)

raw_data = match.group(1)
ansi_regex = chr(27) + chr(91) + r'[0-9;]*[a-zA-Z]'
raw_data = re.sub(ansi_regex, '', raw_data)
raw_data = raw_data.replace(r'\\n', chr(10)).replace(r'\"', '"')

os.makedirs(os.path.dirname(pdf_file), exist_ok=True)
doc = SimpleDocTemplate(pdf_file, pagesize=landscape(letter), rightMargin=30, leftMargin=30, topMargin=35, bottomMargin=35)
story = []
styles = getSampleStyleSheet()

title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=20, spaceAfter=8, textColor=colors.HexColor('#1A365D'))
meta_style = ParagraphStyle('MetaStyle', parent=styles['Normal'], fontSize=9, spaceAfter=12, textColor=colors.HexColor('#4A5568'))
section_style = ParagraphStyle('SectionStyle', parent=styles['Heading2'], fontSize=12, spaceBefore=10, spaceAfter=6, textColor=colors.HexColor('#2B6CB0'))
header_style = ParagraphStyle('HeaderStyle', parent=styles['Normal'], fontSize=8, fontName='Helvetica-Bold', textColor=colors.white)
cell_style = ParagraphStyle('CellStyle', parent=styles['Normal'], fontSize=8, leading=10, wordWrap='CJK')
code_style = ParagraphStyle('CodeStyle', parent=cell_style, fontName='Courier', fontSize=7)

story.append(Paragraph('ENTERPRISE LINUX PATCHING REPORT', title_style))
gen_time = time.strftime("%Y-%m-%d %H:%M:%S UTC")
story.append(Paragraph(f"Generated on: {gen_time}", meta_style))
story.append(Spacer(1, 8))

records = re.split(r'HOST_RECORD:', raw_data)
for record in records:
    if not record.strip():
        continue
    pkg_match = re.search(r'PATCHED_PACKAGES_START(.*?)PATCHED_PACKAGES_END', record, re.DOTALL)
    pkg_lines = []
    if pkg_match:
        pkg_lines = [l.strip() for l in pkg_match.group(1).splitlines() if l.strip()]
        record_meta_part = record.split('PATCHED_PACKAGES_START')[0]
    else:
        record_meta_part = record
        
    lines = record_meta_part.splitlines()
    meta = {}
    
    discovered_host = "Unknown Target"
    for line in lines:
        clean_line = line.strip()
        if ':' in clean_line:
            k, v = clean_line.split(':', 1)
            meta[k.strip()] = v.strip()
            if k.strip() == "HOST_RECORD" and v.strip():
                discovered_host = v.strip()
            
    host_name = discovered_host if discovered_host != "Unknown Target" else meta.get('HOST_RECORD', 'Unknown Target')
    story.append(Paragraph(f"Host Execution Target: {escape(host_name)}", section_style))
    status = meta.get('STATUS', 'FAILED')
    status_color = '#38A169' if status.upper() == 'SUCCESS' else '#E53E3E'
    kernel_change = f"{meta.get('OLD_KERNEL', 'N/A')} -> {meta.get('NEW_KERNEL', 'N/A')}"
    
    summary_data = [
        [Paragraph('Host Target', header_style), Paragraph('Operating System', header_style), 
         Paragraph('Kernel Version Change', header_style), Paragraph('Updated', header_style), 
         Paragraph('Reboot', header_style), Paragraph('Status', header_style)],
        [Paragraph(escape(host_name), cell_style), Paragraph(escape(meta.get('OS', 'Unknown')), cell_style), 
         Paragraph(escape(kernel_change), cell_style), Paragraph(escape(meta.get('UPDATED', 'No')), cell_style), 
         Paragraph(escape(meta.get('REBOOT', 'No')), cell_style), Paragraph(f"<font color='{status_color}'><b>{escape(status)}</b></font>", cell_style)]
    ]
    
    summary_table = Table(summary_data, colWidths=[120, 130, 155, 65, 65, 80])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2B6CB0')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E0')),
        ('PADDING', (0,0), (-1,-1), 5),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE')
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 10))
    
    package_data = [[Paragraph('Package Name', header_style), Paragraph('Last Version', header_style), Paragraph('Updated Version', header_style)]]
    unique_packages = {}
    for p_line in pkg_lines:
        if 'No packages updated.' in p_line:
            break
        parts = p_line.split()
        if not parts or len(parts) < 2:
            continue
        if parts[0] in ['half-installed', 'installed', 'upgraded', 'unpacked', 'half-configured']:
            parts.pop(0)
        if len(parts) >= 2:
            p_name = parts[0].split(':')[0]
            v_val = parts[1]
            if v_val == '<none>':
                v_val = 'N/A'
            if p_name not in unique_packages:
                unique_packages[p_name] = {'old': 'Unknown', 'new': v_val}
            else:
                if unique_packages[p_name]['old'] == 'Unknown' and unique_packages[p_name]['new'] != v_val:
                    unique_packages[p_name]['old'] = unique_packages[p_name]['new']
                    unique_packages[p_name]['new'] = v_val
                else:
                    unique_packages[p_name]['new'] = v_val
                    
    has_packages = False
    for name, vdata in sorted(unique_packages.items()):
        has_packages = True
        package_data.append([Paragraph(escape(name), code_style), Paragraph(escape(vdata['old']), code_style), Paragraph(escape(vdata['new']), code_style)])
        
    if has_packages:
        story.append(Paragraph('<b>Available Package Update Matrix:</b>', cell_style))
        story.append(Spacer(1, 4))
        pkg_table = Table(package_data, colWidths=[240, 150, 150])
        pkg_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#4A5568')),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
            ('PADDING', (0,0), (-1,-1), 4),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F7FAFC')]),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE')
        ]))
        story.append(pkg_table)
    else:
        story.append(Paragraph('<i>System is up to date, no packages available to update.</i>', cell_style))
    story.append(Spacer(1, 15))

doc.build(story)
print("PDF compilation successful.")
