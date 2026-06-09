"""
本体验证器

提供本体一致性检查、完整性验证和合规性验证功能。
"""

from typing import Any, Dict, List, Optional
from loguru import logger

from .ontology_manager import OntologyManager, RDFLIB_AVAILABLE


class ValidationIssue:
    """验证问题"""

    def __init__(
        self,
        issue_type: str,
        severity: str,
        message: str,
        location: Optional[str] = None,
        suggestion: Optional[str] = None,
    ):
        """
        初始化验证问题

        Args:
            issue_type: 问题类型（structure/consistency/completeness）
            severity: 严重程度（error/warning/info）
            message: 问题描述
            location: 问题位置
            suggestion: 修复建议
        """
        self.issue_type = issue_type
        self.severity = severity
        self.message = message
        self.location = location
        self.suggestion = suggestion

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {
            "type": self.issue_type,
            "severity": self.severity,
            "message": self.message,
        }
        if self.location:
            result["location"] = self.location
        if self.suggestion:
            result["suggestion"] = self.suggestion
        return result


class ValidationResult:
    """验证结果"""

    def __init__(self):
        self.issues: List[ValidationIssue] = []
        self.is_valid = True

    def add_issue(self, issue: ValidationIssue):
        """添加问题"""
        self.issues.append(issue)
        if issue.severity == "error":
            self.is_valid = False

    @property
    def errors(self) -> List[ValidationIssue]:
        """获取错误"""
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> List[ValidationIssue]:
        """获取警告"""
        return [i for i in self.issues if i.severity == "warning"]

    @property
    def infos(self) -> List[ValidationIssue]:
        """获取信息"""
        return [i for i in self.issues if i.severity == "info"]

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "is_valid": self.is_valid,
            "errors": len(self.errors),
            "warnings": len(self.warnings),
            "infos": len(self.infos),
            "issues": [i.to_dict() for i in self.issues],
        }


class OntologyValidator:
    """本体验证器"""

    def __init__(self, ontology_manager: OntologyManager):
        """
        初始化本体验证器

        Args:
            ontology_manager: 本体管理器
        """
        self.ontology_manager = ontology_manager

    def validate_all(self) -> ValidationResult:
        """
        执行完整验证

        Returns:
            验证结果
        """
        result = ValidationResult()

        if not RDFLIB_AVAILABLE:
            result.add_issue(ValidationIssue(
                issue_type="system",
                severity="error",
                message="RDFLib not installed. Cannot validate ontology.",
                suggestion="Install RDFLib: pip install rdflib"
            ))
            return result

        # 结构验证
        self._validate_structure(result)

        # 一致性验证
        self._validate_consistency(result)

        # 完整性验证
        self._validate_completeness(result)

        return result

    def _validate_structure(self, result: ValidationResult):
        """
        验证本体结构

        Args:
            result: 验证结果
        """
        if not self.ontology_manager._loaded:
            result.add_issue(ValidationIssue(
                issue_type="structure",
                severity="warning",
                message="Ontology not loaded",
                suggestion="Load ontology before validation"
            ))
            return

        classes = self.ontology_manager.get_classes()

        # 检查是否有类定义
        if not classes:
            result.add_issue(ValidationIssue(
                issue_type="structure",
                severity="error",
                message="No classes defined in ontology",
                suggestion="Add at least one class definition"
            ))

        # 检查类名是否符合命名规范
        for cls in classes:
            name = cls.get("name", "")
            if name and not name[0].isupper():
                result.add_issue(ValidationIssue(
                    issue_type="structure",
                    severity="warning",
                    message=f"Class name '{name}' should start with uppercase",
                    location=f"Class:{name}",
                    suggestion="Rename class to start with uppercase letter"
                ))

        # 检查属性名是否符合命名规范
        properties = self.ontology_manager.get_properties()
        for prop in properties:
            name = prop.get("name", "")
            if name and name[0].isupper():
                result.add_issue(ValidationIssue(
                    issue_type="structure",
                    severity="warning",
                    message=f"Property name '{name}' should start with lowercase (camelCase)",
                    location=f"Property:{name}",
                    suggestion="Rename property to start with lowercase letter"
                ))

        logger.info(f"Structure validation completed: {len(result.issues)} issues found")

    def _validate_consistency(self, result: ValidationResult):
        """
        验证本体一致性

        Args:
            result: 验证结果
        """
        if not self.ontology_manager._loaded:
            return

        properties = self.ontology_manager.get_properties()

        # 检查属性的定义域和值域
        for prop in properties:
            if not prop.get("domain"):
                result.add_issue(ValidationIssue(
                    issue_type="consistency",
                    severity="warning",
                    message=f"Property '{prop['name']}' has no domain defined",
                    location=f"Property:{prop['name']}",
                    suggestion="Define domain for the property"
                ))
            if not prop.get("range"):
                result.add_issue(ValidationIssue(
                    issue_type="consistency",
                    severity="warning",
                    message=f"Property '{prop['name']}' has no range defined",
                    location=f"Property:{prop['name']}",
                    suggestion="Define range for the property"
                ))

        logger.info(f"Consistency validation completed: {len(result.issues)} issues found")

    def _validate_completeness(self, result: ValidationResult):
        """
        验证本体完整性

        Args:
            result: 验证结果
        """
        if not self.ontology_manager._loaded:
            return

        classes = self.ontology_manager.get_classes()

        # 检查是否有孤立的类
        for cls in classes:
            children = cls.get("children", [])
            instances = self.ontology_manager.get_instances(cls["name"])
            if not children and not instances and cls["name"] != "Thing":
                result.add_issue(ValidationIssue(
                    issue_type="completeness",
                    severity="info",
                    message=f"Class '{cls['name']}' has no instances or subclasses",
                    location=f"Class:{cls['name']}",
                    suggestion="Consider adding instances or removing the class"
                ))

        logger.info(f"Completeness validation completed: {len(result.issues)} issues found")

    def generate_report(self) -> str:
        """
        生成验证报告

        Returns:
            验证报告文本
        """
        result = self.validate_all()

        report_lines = [
            "=" * 60,
            "Ontology Validation Report",
            "=" * 60,
            "",
            f"Overall Status: {'PASS' if result.is_valid else 'FAIL'}",
            f"Errors: {len(result.errors)}",
            f"Warnings: {len(result.warnings)}",
            f"Infos: {len(result.infos)}",
            "",
        ]

        if result.errors:
            report_lines.append("-" * 40)
            report_lines.append("ERRORS:")
            report_lines.append("-" * 40)
            for error in result.errors:
                report_lines.append(f"  [{error.issue_type}] {error.message}")
                if error.location:
                    report_lines.append(f"    Location: {error.location}")
                if error.suggestion:
                    report_lines.append(f"    Suggestion: {error.suggestion}")
                report_lines.append("")

        if result.warnings:
            report_lines.append("-" * 40)
            report_lines.append("WARNINGS:")
            report_lines.append("-" * 40)
            for warning in result.warnings:
                report_lines.append(f"  [{warning.issue_type}] {warning.message}")
                if warning.location:
                    report_lines.append(f"    Location: {warning.location}")
                if warning.suggestion:
                    report_lines.append(f"    Suggestion: {warning.suggestion}")
                report_lines.append("")

        if result.infos:
            report_lines.append("-" * 40)
            report_lines.append("INFORMATION:")
            report_lines.append("-" * 40)
            for info in result.infos:
                report_lines.append(f"  [{info.issue_type}] {info.message}")
                if info.location:
                    report_lines.append(f"    Location: {info.location}")
                report_lines.append("")

        report_lines.append("=" * 60)

        return "\n".join(report_lines)
