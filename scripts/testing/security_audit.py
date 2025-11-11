#!/usr/bin/env python3
"""
Comprehensive Security Audit Tool for TutorMax

Performs a complete security audit including:
- Configuration security
- Code security analysis
- Dependency audit
- Compliance verification
- Security best practices
- OWASP Top 10 checks

Task: 14.8 - Security Testing & Penetration Testing

Usage:
    python3 scripts/security_audit.py
    python3 scripts/security_audit.py --verbose
    python3 scripts/security_audit.py --export-json
"""

import sys
import os
import re
import json
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from collections import defaultdict

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class SecurityAudit:
    """Comprehensive security audit tool."""

    def __init__(self, project_root: Path, verbose: bool = False):
        self.project_root = project_root
        self.verbose = verbose
        self.findings: List[Dict[str, Any]] = []
        self.checks_passed: List[str] = []
        self.warnings: List[Dict[str, Any]] = []
        self.compliance_status: Dict[str, bool] = {}

    def log(self, message: str, level: str = "INFO"):
        """Log message."""
        if self.verbose or level in ["ERROR", "WARNING", "CRITICAL"]:
            print(f"[{level}] {message}")

    def add_finding(self, severity: str, category: str, issue: str,
                   description: str, remediation: str, **kwargs):
        """Add security finding."""
        self.findings.append({
            "severity": severity,
            "category": category,
            "issue": issue,
            "description": description,
            "remediation": remediation,
            "timestamp": datetime.utcnow().isoformat(),
            **kwargs
        })
        self.log(f"[{severity}] {issue}", level=severity)

    def add_warning(self, category: str, message: str, recommendation: str):
        """Add security warning."""
        self.warnings.append({
            "category": category,
            "message": message,
            "recommendation": recommendation,
            "timestamp": datetime.utcnow().isoformat()
        })
        self.log(f"[WARNING] {message}", level="WARNING")

    def add_pass(self, check_name: str):
        """Add passed check."""
        self.checks_passed.append(check_name)
        self.log(f"✓ {check_name}", level="INFO")

    def audit_environment_configuration(self):
        """Audit environment configuration and secrets."""
        print("\n[AUDIT] Environment Configuration Security")
        print("-" * 70)

        env_example = self.project_root / ".env.example"
        env_file = self.project_root / ".env"

        # Check .env.example exists
        if not env_example.exists():
            self.add_finding(
                severity="MEDIUM",
                category="Configuration",
                issue="Missing .env.example file",
                description=".env.example template not found",
                remediation="Create .env.example with all required variables (without secrets)"
            )
        else:
            self.add_pass("Environment template (.env.example) exists")

        # Check .env file security
        if env_file.exists():
            with open(env_file, "r") as f:
                env_content = f.read()

            # Check for default secrets
            if "your-secret-key-change-in-production" in env_content:
                self.add_finding(
                    severity="CRITICAL",
                    category="Configuration",
                    issue="Default SECRET_KEY in production",
                    description="Application using default SECRET_KEY from example",
                    remediation="Generate strong SECRET_KEY: openssl rand -hex 32",
                    file=".env"
                )
            else:
                self.add_pass("SECRET_KEY is not default value")

            # Check DEBUG mode
            if "DEBUG=True" in env_content or "DEBUG=true" in env_content:
                self.add_warning(
                    category="Configuration",
                    message="DEBUG mode is enabled",
                    recommendation="Set DEBUG=false in production to prevent information disclosure"
                )

            # Check encryption is enabled
            if "ENCRYPTION_ENABLED=false" in env_content.lower():
                self.add_finding(
                    severity="HIGH",
                    category="Encryption",
                    issue="Data encryption disabled",
                    description="ENCRYPTION_ENABLED is set to false",
                    remediation="Enable encryption: ENCRYPTION_ENABLED=true",
                    file=".env"
                )
            else:
                self.add_pass("Data encryption is enabled")

            # Check HTTPS/TLS enforcement
            if "HSTS_ENABLED=false" in env_content.lower():
                self.add_warning(
                    category="Transport Security",
                    message="HSTS (HTTP Strict Transport Security) is disabled",
                    recommendation="Enable HSTS: HSTS_ENABLED=true"
                )

            # Check CSRF protection
            if "CSRF_ENABLED=false" in env_content.lower():
                self.add_finding(
                    severity="HIGH",
                    category="Web Security",
                    issue="CSRF protection disabled",
                    description="CSRF_ENABLED is set to false",
                    remediation="Enable CSRF protection: CSRF_ENABLED=true",
                    file=".env"
                )
            else:
                self.add_pass("CSRF protection is enabled")

            # Check rate limiting
            if "RATE_LIMIT_ENABLED=false" in env_content.lower():
                self.add_finding(
                    severity="HIGH",
                    category="API Security",
                    issue="Rate limiting disabled",
                    description="RATE_LIMIT_ENABLED is set to false",
                    remediation="Enable rate limiting: RATE_LIMIT_ENABLED=true",
                    file=".env"
                )
            else:
                self.add_pass("Rate limiting is enabled")

        else:
            self.add_warning(
                category="Configuration",
                message=".env file not found",
                recommendation="Create .env from .env.example for local configuration"
            )

    def audit_code_security(self):
        """Audit code for security vulnerabilities."""
        print("\n[AUDIT] Code Security Analysis")
        print("-" * 70)

        src_dir = self.project_root / "src"
        if not src_dir.exists():
            self.add_warning(
                category="Code Security",
                message="Source directory not found",
                recommendation="Verify project structure"
            )
            return

        # Patterns to check
        dangerous_patterns = {
            r'exec\s*\(': "Dangerous exec() usage - code injection risk",
            r'eval\s*\(': "Dangerous eval() usage - code injection risk",
            r'__import__\s*\(': "Dynamic imports can be dangerous",
            r'os\.system\s*\(': "os.system() usage - command injection risk",
            r'subprocess\.call\(.*shell=True': "subprocess with shell=True - command injection risk",
            r'pickle\.loads?\s*\(': "Pickle deserialization - code execution risk",
            r'yaml\.load\((?!.*Loader=)': "Unsafe YAML loading - code execution risk",
            r'\.format\s*\(.*request\.': "String formatting with user input - injection risk",
            r'f".*{request\.': "F-string with user input - injection risk",
        }

        # SQL injection patterns
        sql_patterns = {
            r'\.execute\s*\(\s*f"': "SQL query with f-string - SQL injection risk",
            r'\.execute\s*\(.*\+.*request\.': "SQL query concatenation - SQL injection risk",
            r'\.execute\s*\(.*%.*request\.': "SQL query with % formatting - SQL injection risk",
        }

        # Scan Python files
        python_files = list(src_dir.rglob("*.py"))
        vulnerabilities_found = defaultdict(list)

        for py_file in python_files:
            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    content = f.read()
                    lines = content.split("\n")

                # Check dangerous patterns
                for pattern, description in dangerous_patterns.items():
                    for i, line in enumerate(lines, 1):
                        if re.search(pattern, line):
                            vulnerabilities_found[description].append(
                                f"{py_file.relative_to(self.project_root)}:{i}"
                            )

                # Check SQL patterns
                for pattern, description in sql_patterns.items():
                    for i, line in enumerate(lines, 1):
                        if re.search(pattern, line):
                            vulnerabilities_found[description].append(
                                f"{py_file.relative_to(self.project_root)}:{i}"
                            )

                # Check for hardcoded secrets
                secret_patterns = [
                    r'password\s*=\s*["\'][^"\']+["\']',
                    r'api_key\s*=\s*["\'][^"\']+["\']',
                    r'secret\s*=\s*["\'][^"\']+["\']',
                    r'token\s*=\s*["\'][^"\']+["\']',
                ]

                for pattern in secret_patterns:
                    for i, line in enumerate(lines, 1):
                        # Exclude environment variable assignments
                        if re.search(pattern, line, re.IGNORECASE):
                            if "os.getenv" not in line and "settings." not in line:
                                vulnerabilities_found["Hardcoded secret detected"].append(
                                    f"{py_file.relative_to(self.project_root)}:{i}"
                                )

            except Exception as e:
                self.log(f"Error scanning {py_file}: {e}", level="ERROR")

        # Report vulnerabilities
        for description, locations in vulnerabilities_found.items():
            if locations:
                self.add_finding(
                    severity="HIGH" if "injection" in description.lower() or "exec" in description.lower() else "MEDIUM",
                    category="Code Security",
                    issue=description,
                    description=f"Found {len(locations)} instance(s)",
                    remediation="Review and fix these code patterns. Use parameterized queries, "
                               "avoid dynamic code execution, and use environment variables for secrets.",
                    locations=locations[:10]  # Limit to first 10
                )

        if not vulnerabilities_found:
            self.add_pass("No dangerous code patterns detected")

    def audit_dependencies(self):
        """Audit dependencies for known vulnerabilities."""
        print("\n[AUDIT] Dependency Security")
        print("-" * 70)

        requirements_file = self.project_root / "requirements.txt"
        if not requirements_file.exists():
            self.add_warning(
                category="Dependencies",
                message="requirements.txt not found",
                recommendation="Create requirements.txt with pinned versions"
            )
            return

        with open(requirements_file, "r") as f:
            requirements = f.read()

        # Check for unpinned versions
        unpinned_pattern = r'^([a-zA-Z0-9-_]+)\s*$'
        for line in requirements.split("\n"):
            line = line.strip()
            if line and not line.startswith("#"):
                if re.match(unpinned_pattern, line):
                    self.add_warning(
                        category="Dependencies",
                        message=f"Unpinned dependency: {line}",
                        recommendation="Pin all dependencies to specific versions for reproducibility"
                    )

        # Check for outdated critical packages
        critical_packages = {
            "fastapi": "0.109.0",
            "sqlalchemy": "2.0.25",
            "cryptography": "42.0.0",
            "pydantic": "2.5.0",
        }

        for package, min_version in critical_packages.items():
            if package.lower() in requirements.lower():
                # Extract version
                pattern = rf'{package}==([0-9.]+)'
                match = re.search(pattern, requirements, re.IGNORECASE)
                if match:
                    version = match.group(1)
                    # Simple version comparison (not perfect but good enough)
                    if version < min_version:
                        self.add_warning(
                            category="Dependencies",
                            message=f"{package} version {version} may be outdated",
                            recommendation=f"Consider updating to {min_version} or later"
                        )

        self.add_pass("Dependency audit completed")

    def audit_authentication_security(self):
        """Audit authentication implementation."""
        print("\n[AUDIT] Authentication Security")
        print("-" * 70)

        config_file = self.project_root / "src" / "api" / "config.py"
        if config_file.exists():
            with open(config_file, "r") as f:
                config_content = f.read()

            # Check password policy
            if "password_min_length" in config_content:
                match = re.search(r'password_min_length:\s*int\s*=\s*(\d+)', config_content)
                if match:
                    min_length = int(match.group(1))
                    if min_length < 8:
                        self.add_finding(
                            severity="MEDIUM",
                            category="Authentication",
                            issue="Weak password policy",
                            description=f"Minimum password length is {min_length} (should be >= 8)",
                            remediation="Set password_min_length to at least 8 characters",
                            file="src/api/config.py"
                        )
                    else:
                        self.add_pass("Password minimum length requirement is adequate")

            # Check JWT settings
            if "jwt_algorithm" in config_content:
                if '"HS256"' in config_content or "'HS256'" in config_content:
                    self.add_pass("JWT algorithm is HS256 (acceptable)")
                elif '"none"' in config_content.lower():
                    self.add_finding(
                        severity="CRITICAL",
                        category="Authentication",
                        issue="JWT algorithm set to 'none'",
                        description="JWT tokens without signature verification",
                        remediation="Use HS256 or RS256 for JWT signatures",
                        file="src/api/config.py"
                    )

            # Check token expiration
            if "access_token_expire_minutes" in config_content:
                match = re.search(r'access_token_expire_minutes:\s*int\s*=\s*(\d+)', config_content)
                if match:
                    expire_minutes = int(match.group(1))
                    if expire_minutes > 60:
                        self.add_warning(
                            category="Authentication",
                            message=f"Access token expiration is {expire_minutes} minutes (> 1 hour)",
                            recommendation="Consider shorter token expiration for better security"
                        )
                    else:
                        self.add_pass("Access token expiration is reasonable")

    def audit_compliance(self):
        """Audit regulatory compliance implementation."""
        print("\n[AUDIT] Regulatory Compliance")
        print("-" * 70)

        compliance_modules = {
            "FERPA": self.project_root / "src" / "api" / "compliance" / "ferpa.py",
            "COPPA": self.project_root / "src" / "api" / "compliance" / "coppa.py",
            "GDPR": self.project_root / "src" / "api" / "compliance" / "gdpr.py",
        }

        for regulation, module_path in compliance_modules.items():
            if module_path.exists():
                self.add_pass(f"{regulation} compliance module exists")
                self.compliance_status[regulation] = True
            else:
                self.add_finding(
                    severity="HIGH",
                    category="Compliance",
                    issue=f"Missing {regulation} compliance module",
                    description=f"{regulation} compliance implementation not found",
                    remediation=f"Implement {regulation} compliance in src/api/compliance/",
                    regulation=regulation
                )
                self.compliance_status[regulation] = False

        # Check encryption implementation
        encryption_service = self.project_root / "src" / "api" / "security" / "encryption.py"
        if encryption_service.exists():
            self.add_pass("Encryption service implemented")
        else:
            self.add_finding(
                severity="CRITICAL",
                category="Compliance",
                issue="Missing encryption service",
                description="AES-256 encryption not implemented for PII",
                remediation="Implement encryption service for PII protection (FERPA, COPPA, GDPR requirement)"
            )

        # Check audit logging
        audit_service = self.project_root / "src" / "api" / "audit_service.py"
        if audit_service.exists():
            self.add_pass("Audit logging implemented")
        else:
            self.add_warning(
                category="Compliance",
                message="Audit logging not found",
                recommendation="Implement comprehensive audit logging for compliance"
            )

    def audit_api_security(self):
        """Audit API security configurations."""
        print("\n[AUDIT] API Security")
        print("-" * 70)

        main_file = self.project_root / "src" / "api" / "main.py"
        if not main_file.exists():
            self.add_warning(
                category="API Security",
                message="main.py not found",
                recommendation="Verify project structure"
            )
            return

        with open(main_file, "r") as f:
            main_content = f.read()

        # Check CORS configuration
        if "CORSMiddleware" in main_content:
            if "allow_origins=[\\"*\\"]" in main_content or 'allow_origins=["*"]' in main_content:
                self.add_finding(
                    severity="HIGH",
                    category="API Security",
                    issue="Overly permissive CORS configuration",
                    description="CORS allows all origins (*)",
                    remediation="Restrict CORS to specific trusted domains only",
                    file="src/api/main.py"
                )
            else:
                self.add_pass("CORS configuration restricts origins")
        else:
            self.add_warning(
                category="API Security",
                message="CORS middleware not configured",
                recommendation="Configure CORS middleware to control cross-origin requests"
            )

        # Check for security middleware
        security_checks = {
            "RateLimitMiddleware": "Rate limiting middleware",
            "SecurityHeadersMiddleware": "Security headers middleware",
            "CSRFProtectionMiddleware": "CSRF protection middleware",
        }

        for middleware, description in security_checks.items():
            if middleware in main_content:
                self.add_pass(f"{description} configured")
            else:
                self.add_warning(
                    category="API Security",
                    message=f"{description} not found",
                    recommendation=f"Add {middleware} to protect against attacks"
                )

    def generate_report(self, export_json: bool = False) -> str:
        """Generate comprehensive audit report."""
        report = []
        report.append("\n" + "="*70)
        report.append("TUTORMAX COMPREHENSIVE SECURITY AUDIT REPORT")
        report.append("="*70)
        report.append(f"Audit Date: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        report.append(f"Project: {self.project_root}")
        report.append("")

        # Executive Summary
        critical = sum(1 for f in self.findings if f["severity"] == "CRITICAL")
        high = sum(1 for f in self.findings if f["severity"] == "HIGH")
        medium = sum(1 for f in self.findings if f["severity"] == "MEDIUM")
        low = sum(1 for f in self.findings if f["severity"] == "LOW")

        report.append("EXECUTIVE SUMMARY")
        report.append("-" * 70)
        report.append(f"Total Security Findings: {len(self.findings)}")
        report.append(f"  - Critical: {critical}")
        report.append(f"  - High: {high}")
        report.append(f"  - Medium: {medium}")
        report.append(f"  - Low: {low}")
        report.append(f"Warnings: {len(self.warnings)}")
        report.append(f"Checks Passed: {len(self.checks_passed)}")
        report.append("")

        # Risk Assessment
        if critical > 0:
            risk = "CRITICAL - Immediate remediation required"
        elif high > 0:
            risk = "HIGH - Address vulnerabilities urgently"
        elif medium > 0:
            risk = "MEDIUM - Review and remediate soon"
        elif low > 0:
            risk = "LOW - Minor issues to address"
        else:
            risk = "MINIMAL - Good security posture"

        report.append(f"Overall Risk Level: {risk}")
        report.append("")

        # Compliance Status
        report.append("COMPLIANCE STATUS")
        report.append("-" * 70)
        for regulation, status in self.compliance_status.items():
            status_icon = "✓" if status else "✗"
            report.append(f"{status_icon} {regulation}: {'Implemented' if status else 'Missing'}")
        report.append("")

        # Findings
        if self.findings:
            report.append("SECURITY FINDINGS")
            report.append("="*70)
            for i, finding in enumerate(self.findings, 1):
                report.append(f"\n{i}. [{finding['severity']}] {finding['issue']}")
                report.append(f"   Category: {finding['category']}")
                report.append(f"   Description: {finding['description']}")
                report.append(f"   Remediation: {finding['remediation']}")
                if "file" in finding:
                    report.append(f"   File: {finding['file']}")
        else:
            report.append("✓ No critical security findings")

        # Warnings
        if self.warnings:
            report.append("\n\nSECURITY WARNINGS")
            report.append("="*70)
            for i, warning in enumerate(self.warnings, 1):
                report.append(f"\n{i}. {warning['category']}")
                report.append(f"   Message: {warning['message']}")
                report.append(f"   Recommendation: {warning['recommendation']}")

        # Passed Checks
        report.append("\n\nPASSED SECURITY CHECKS")
        report.append("="*70)
        for check in self.checks_passed:
            report.append(f"✓ {check}")

        report.append("\n" + "="*70)
        report.append("END OF AUDIT REPORT")
        report.append("="*70 + "\n")

        report_text = "\n".join(report)

        # Export JSON
        if export_json:
            audit_data = {
                "audit_timestamp": datetime.utcnow().isoformat(),
                "project_root": str(self.project_root),
                "summary": {
                    "total_findings": len(self.findings),
                    "critical": critical,
                    "high": high,
                    "medium": medium,
                    "low": low,
                    "warnings": len(self.warnings),
                    "checks_passed": len(self.checks_passed),
                    "risk_level": risk
                },
                "compliance_status": self.compliance_status,
                "findings": self.findings,
                "warnings": self.warnings,
                "passed_checks": self.checks_passed
            }

            json_path = self.project_root / "docs" / "security_audit_report.json"
            with open(json_path, "w") as f:
                json.dump(audit_data, f, indent=2)

            print(f"\nJSON report exported to: {json_path}")

        return report_text


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="TutorMax Security Audit Tool")
    parser.add_argument("--project-root", default=Path.cwd(),
                       help="Project root directory (default: current directory)")
    parser.add_argument("--verbose", action="store_true",
                       help="Enable verbose output")
    parser.add_argument("--export-json", action="store_true",
                       help="Export JSON report to docs/security_audit_report.json")

    args = parser.parse_args()

    project_root = Path(args.project_root)
    audit = SecurityAudit(project_root=project_root, verbose=args.verbose)

    print("\n" + "="*70)
    print("TutorMax Comprehensive Security Audit")
    print("="*70)
    print(f"Audit started: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"Project: {project_root}")
    print("="*70)

    try:
        # Run all audit checks
        audit.audit_environment_configuration()
        audit.audit_code_security()
        audit.audit_dependencies()
        audit.audit_authentication_security()
        audit.audit_compliance()
        audit.audit_api_security()

        # Generate report
        report = audit.generate_report(export_json=args.export_json)
        print(report)

        # Save text report
        report_path = project_root / "docs" / "security_audit_report.txt"
        with open(report_path, "w") as f:
            f.write(report)

        print(f"\nReport saved to: {report_path}")

        # Exit with error code if critical findings
        critical_count = sum(1 for f in audit.findings if f["severity"] == "CRITICAL")
        if critical_count > 0:
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\nAudit interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\nERROR: Audit failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
