#!/usr/bin/env python3
"""
Comprehensive Quality Assurance Testing Suite
Checks for code quality, naming conventions, error handling, and consistency
"""

import os
import ast
import json
import sys
import re
from typing import Dict, List, Any, Set
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.append('/Users/aditya/Documents/Tailer/tailer_v2')

class QualityAssuranceTester:
    """Comprehensive quality assurance testing"""
    
    def __init__(self):
        self.project_root = Path('/Users/aditya/Documents/Tailer/tailer_v2')
        self.test_results = {
            "timestamp": datetime.now().isoformat(),
            "code_quality": {
                "import_consistency": {"issues": [], "compliant": []},
                "naming_conventions": {"issues": [], "compliant": []},
                "error_handling": {"issues": [], "compliant": []},
                "docstring_coverage": {"missing": [], "present": []},
                "unused_imports": {"files": [], "total_unused": 0}
            },
            "api_consistency": {
                "endpoint_naming": {"issues": [], "compliant": []},
                "response_models": {"issues": [], "compliant": []},
                "authentication": {"issues": [], "compliant": []}
            },
            "database_consistency": {
                "model_relationships": {"issues": [], "compliant": []},
                "naming_conventions": {"issues": [], "compliant": []},
                "field_consistency": {"issues": [], "compliant": []}
            },
            "file_structure": {
                "missing_files": [],
                "organization_issues": [],
                "duplicate_functionality": []
            },
            "summary": {}
        }
    
    def run_comprehensive_qa(self):
        """Run all quality assurance checks"""
        print("=== COMPREHENSIVE QUALITY ASSURANCE TESTING ===\n")
        
        try:
            print("1. Checking code quality...")
            self._check_code_quality()
            
            print("2. Checking API consistency...")
            self._check_api_consistency()
            
            print("3. Checking database consistency...")
            self._check_database_consistency()
            
            print("4. Checking file structure...")
            self._check_file_structure()
            
            print("5. Checking import consistency...")
            self._check_import_consistency()
            
            print("6. Checking naming conventions...")
            self._check_naming_conventions()
            
            print("7. Checking error handling patterns...")
            self._check_error_handling()
            
            print("8. Generating quality report...")
            self._generate_quality_report()
            
            return True
            
        except Exception as e:
            print(f"❌ Quality assurance testing failed: {e}")
            return False
    
    def _check_code_quality(self):
        """Check code quality across Python files"""
        python_files = list(self.project_root.rglob("*.py"))
        
        for file_path in python_files:
            if "test_" in str(file_path) or "__pycache__" in str(file_path):
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check for docstrings
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                        if ast.get_docstring(node):
                            self.test_results["code_quality"]["docstring_coverage"]["present"].append(
                                f"{file_path.name}:{node.name}"
                            )
                        else:
                            self.test_results["code_quality"]["docstring_coverage"]["missing"].append(
                                f"{file_path.name}:{node.name}"
                            )
                
                # Check for unused imports (basic check)
                imports = re.findall(r'^(?:from .+ import .+|import .+)$', content, re.MULTILINE)
                for imp in imports:
                    imported_name = imp.split()[-1].split('.')[0]
                    if imported_name not in content.replace(imp, ''):
                        self.test_results["code_quality"]["unused_imports"]["files"].append(
                            f"{file_path.name}: {imp}"
                        )
                        self.test_results["code_quality"]["unused_imports"]["total_unused"] += 1
                
            except Exception as e:
                print(f"  ⚠️  Could not analyze {file_path.name}: {e}")
        
        print(f"  ✅ Code quality check completed")
        print(f"     - Docstring coverage: {len(self.test_results['code_quality']['docstring_coverage']['present'])} present, {len(self.test_results['code_quality']['docstring_coverage']['missing'])} missing")
        print(f"     - Unused imports: {self.test_results['code_quality']['unused_imports']['total_unused']} found")
    
    def _check_api_consistency(self):
        """Check API endpoint consistency"""
        api_files = list((self.project_root / "app" / "api" / "routes").glob("*.py"))
        
        endpoint_patterns = []
        authentication_patterns = []
        
        for file_path in api_files:
            if file_path.name == "__init__.py":
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check endpoint naming
                endpoints = re.findall(r'@router\.(get|post|put|delete)\("([^"]+)"', content)
                for method, endpoint in endpoints:
                    endpoint_patterns.append((file_path.name, method, endpoint))
                    
                    # Check naming convention
                    if not endpoint.startswith("/") or " " in endpoint:
                        self.test_results["api_consistency"]["endpoint_naming"]["issues"].append(
                            f"{file_path.name}: {endpoint} - Invalid naming"
                        )
                    else:
                        self.test_results["api_consistency"]["endpoint_naming"]["compliant"].append(
                            f"{file_path.name}: {endpoint}"
                        )
                
                # Check authentication usage
                if "Depends(get_current_user)" in content:
                    auth_endpoints = len(re.findall(r'get_current_user', content))
                    authentication_patterns.append((file_path.name, auth_endpoints))
                    self.test_results["api_consistency"]["authentication"]["compliant"].append(
                        f"{file_path.name}: {auth_endpoints} protected endpoints"
                    )
                
            except Exception as e:
                print(f"  ⚠️  Could not analyze API file {file_path.name}: {e}")
        
        print(f"  ✅ API consistency check completed")
        print(f"     - Endpoints found: {len(endpoint_patterns)}")
        print(f"     - Files with authentication: {len(authentication_patterns)}")
    
    def _check_database_consistency(self):
        """Check database model consistency"""
        try:
            database_file = self.project_root / "app" / "models" / "database.py"
            
            with open(database_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for consistent UUID usage
            uuid_patterns = re.findall(r'Column\(GUID\(\)', content)
            id_patterns = re.findall(r'id = Column\(GUID\(\)', content)
            
            # Check for relationship consistency
            relationships = re.findall(r'relationship\("([^"]+)"', content)
            back_populates = re.findall(r'back_populates="([^"]+)"', content)
            
            self.test_results["database_consistency"]["model_relationships"]["compliant"].extend(relationships)
            
            # Check naming conventions in models
            class_names = re.findall(r'class ([A-Z][a-zA-Z]+)\(Base\):', content)
            for class_name in class_names:
                if class_name[0].isupper() and not "_" in class_name:
                    self.test_results["database_consistency"]["naming_conventions"]["compliant"].append(class_name)
                else:
                    self.test_results["database_consistency"]["naming_conventions"]["issues"].append(
                        f"Class {class_name} doesn't follow PascalCase"
                    )
            
            print(f"  ✅ Database consistency check completed")
            print(f"     - Model classes found: {len(class_names)}")
            print(f"     - Relationships found: {len(relationships)}")
            
        except Exception as e:
            print(f"  ❌ Database consistency check failed: {e}")
    
    def _check_file_structure(self):
        """Check project file structure"""
        required_files = [
            "app/main.py",
            "app/config/settings.py",
            "app/models/database.py",
            "app/services/database_service.py",
            "app/api/routes/auth.py",
            "requirements.txt",
            "README.md"
        ]
        
        missing_files = []
        for file_path in required_files:
            full_path = self.project_root / file_path
            if not full_path.exists():
                missing_files.append(file_path)
        
        self.test_results["file_structure"]["missing_files"] = missing_files
        
        # Check for proper module structure
        service_files = list((self.project_root / "app" / "services").glob("*.py"))
        api_files = list((self.project_root / "app" / "api" / "routes").glob("*.py"))
        
        if len(service_files) < 5:
            self.test_results["file_structure"]["organization_issues"].append(
                f"Expected more service files, found {len(service_files)}"
            )
        
        if len(api_files) < 5:
            self.test_results["file_structure"]["organization_issues"].append(
                f"Expected more API route files, found {len(api_files)}"
            )
        
        print(f"  ✅ File structure check completed")
        print(f"     - Missing required files: {len(missing_files)}")
        print(f"     - Organization issues: {len(self.test_results['file_structure']['organization_issues'])}")
    
    def _check_import_consistency(self):
        """Check import statement consistency"""
        python_files = list(self.project_root.rglob("*.py"))
        
        import_patterns = {
            "relative_imports": [],
            "absolute_imports": [],
            "inconsistent_patterns": []
        }
        
        for file_path in python_files:
            if "__pycache__" in str(file_path):
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Find import patterns
                relative_imports = re.findall(r'^from app\..+ import', content, re.MULTILINE)
                absolute_imports = re.findall(r'^import [^.]+$', content, re.MULTILINE)
                
                if relative_imports and absolute_imports:
                    import_patterns["inconsistent_patterns"].append(file_path.name)
                
                import_patterns["relative_imports"].extend(relative_imports)
                import_patterns["absolute_imports"].extend(absolute_imports)
                
            except Exception as e:
                print(f"  ⚠️  Could not check imports in {file_path.name}: {e}")
        
        self.test_results["code_quality"]["import_consistency"] = import_patterns
        
        print(f"  ✅ Import consistency check completed")
        print(f"     - Files with mixed import styles: {len(import_patterns['inconsistent_patterns'])}")
    
    def _check_naming_conventions(self):
        """Check naming conventions across the codebase"""
        python_files = list(self.project_root.rglob("*.py"))
        
        naming_issues = []
        compliant_names = []
        
        for file_path in python_files:
            if "__pycache__" in str(file_path):
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        # Check function naming (snake_case)
                        if re.match(r'^[a-z_][a-z0-9_]*$', node.name):
                            compliant_names.append(f"function:{node.name}")
                        else:
                            naming_issues.append(f"{file_path.name}:function:{node.name} - Not snake_case")
                    
                    elif isinstance(node, ast.ClassDef):
                        # Check class naming (PascalCase)
                        if re.match(r'^[A-Z][a-zA-Z0-9]*$', node.name):
                            compliant_names.append(f"class:{node.name}")
                        else:
                            naming_issues.append(f"{file_path.name}:class:{node.name} - Not PascalCase")
                
            except Exception as e:
                print(f"  ⚠️  Could not check naming in {file_path.name}: {e}")
        
        self.test_results["code_quality"]["naming_conventions"]["issues"] = naming_issues
        self.test_results["code_quality"]["naming_conventions"]["compliant"] = compliant_names
        
        print(f"  ✅ Naming conventions check completed")
        print(f"     - Naming issues: {len(naming_issues)}")
        print(f"     - Compliant names: {len(compliant_names)}")
    
    def _check_error_handling(self):
        """Check error handling patterns"""
        python_files = list(self.project_root.rglob("*.py"))
        
        error_handling_patterns = {
            "try_catch_blocks": 0,
            "custom_exceptions": [],
            "logging_usage": 0,
            "files_without_error_handling": []
        }
        
        for file_path in python_files:
            if "__pycache__" in str(file_path) or "test_" in str(file_path):
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Count try-except blocks
                try_blocks = len(re.findall(r'\btry\s*:', content))
                error_handling_patterns["try_catch_blocks"] += try_blocks
                
                # Check for logging usage
                if "logger." in content or "logging." in content:
                    error_handling_patterns["logging_usage"] += 1
                
                # Check for custom exceptions
                custom_exceptions = re.findall(r'class ([A-Z][a-zA-Z]*Error|[A-Z][a-zA-Z]*Exception)', content)
                error_handling_patterns["custom_exceptions"].extend(custom_exceptions)
                
                # Files without error handling
                if try_blocks == 0 and "Error" not in content and len(content) > 500:
                    error_handling_patterns["files_without_error_handling"].append(file_path.name)
                
            except Exception as e:
                print(f"  ⚠️  Could not check error handling in {file_path.name}: {e}")
        
        self.test_results["code_quality"]["error_handling"] = error_handling_patterns
        
        print(f"  ✅ Error handling check completed")
        print(f"     - Try-catch blocks: {error_handling_patterns['try_catch_blocks']}")
        print(f"     - Files with logging: {error_handling_patterns['logging_usage']}")
        print(f"     - Custom exceptions: {len(error_handling_patterns['custom_exceptions'])}")
    
    def _generate_quality_report(self):
        """Generate comprehensive quality report"""
        report_path = self.project_root / "reports" / "quality_assurance_report.json"
        
        # Calculate summary metrics
        total_issues = (
            len(self.test_results["code_quality"]["naming_conventions"]["issues"]) +
            len(self.test_results["code_quality"]["docstring_coverage"]["missing"]) +
            len(self.test_results["api_consistency"]["endpoint_naming"]["issues"]) +
            len(self.test_results["database_consistency"]["naming_conventions"]["issues"]) +
            len(self.test_results["file_structure"]["missing_files"]) +
            len(self.test_results["file_structure"]["organization_issues"])
        )
        
        total_compliant = (
            len(self.test_results["code_quality"]["naming_conventions"]["compliant"]) +
            len(self.test_results["code_quality"]["docstring_coverage"]["present"]) +
            len(self.test_results["api_consistency"]["endpoint_naming"]["compliant"]) +
            len(self.test_results["database_consistency"]["naming_conventions"]["compliant"])
        )
        
        quality_score = (total_compliant / (total_compliant + total_issues)) * 100 if (total_compliant + total_issues) > 0 else 100
        
        self.test_results["summary"] = {
            "overall_quality_score": f"{quality_score:.1f}%",
            "total_issues_found": total_issues,
            "total_compliant_items": total_compliant,
            "critical_issues": len(self.test_results["file_structure"]["missing_files"]),
            "code_quality_grade": "A" if quality_score >= 90 else "B" if quality_score >= 80 else "C" if quality_score >= 70 else "D" if quality_score >= 60 else "F",
            "recommendations": self._generate_recommendations()
        }
        
        # Write report
        with open(report_path, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        
        print(f"\n=== QUALITY ASSURANCE SUMMARY ===")
        print(f"Overall Quality Score: {quality_score:.1f}%")
        print(f"Code Quality Grade: {self.test_results['summary']['code_quality_grade']}")
        print(f"Total Issues Found: {total_issues}")
        print(f"Critical Issues: {self.test_results['summary']['critical_issues']}")
        print(f"Report saved to: {report_path}")
        
        if self.test_results['summary']['recommendations']:
            print(f"\nTop Recommendations:")
            for i, rec in enumerate(self.test_results['summary']['recommendations'][:3], 1):
                print(f"  {i}. {rec}")
    
    def _generate_recommendations(self):
        """Generate improvement recommendations"""
        recommendations = []
        
        if len(self.test_results["code_quality"]["docstring_coverage"]["missing"]) > 10:
            recommendations.append("Add docstrings to functions and classes for better documentation")
        
        if self.test_results["code_quality"]["unused_imports"]["total_unused"] > 5:
            recommendations.append("Remove unused imports to clean up codebase")
        
        if len(self.test_results["file_structure"]["missing_files"]) > 0:
            recommendations.append("Add missing required files for project completeness")
        
        if len(self.test_results["code_quality"]["naming_conventions"]["issues"]) > 5:
            recommendations.append("Fix naming convention violations for consistency")
        
        if len(self.test_results["code_quality"]["error_handling"]["files_without_error_handling"]) > 3:
            recommendations.append("Add error handling to files lacking try-catch blocks")
        
        return recommendations


def main():
    """Main QA execution"""
    tester = QualityAssuranceTester()
    success = tester.run_comprehensive_qa()
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)