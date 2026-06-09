#!/usr/bin/env python
"""
本体管理脚本

用于管理股票市场本体的命令行工具。
"""

import argparse
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.app.core.ontology import (
    get_ontology_manager,
    get_ontology_validator,
    STOCK_ONTOLOGY_SCHEMA,
)


def load_ontology(args):
    """加载本体"""
    manager = get_ontology_manager(args.dir)
    manager.load_all_modules()
    stats = manager.get_statistics()
    print(f"Ontology loaded successfully!")
    print(f"  Classes: {stats.get('classes', 0)}")
    print(f"  Object Properties: {stats.get('object_properties', 0)}")
    print(f"  Data Properties: {stats.get('data_properties', 0)}")
    print(f"  Triples: {stats.get('triples', 0)}")


def list_classes(args):
    """列出所有类"""
    manager = get_ontology_manager(args.dir)
    manager.load_all_modules()
    classes = manager.get_classes()

    print(f"\nClasses ({len(classes)}):")
    print("-" * 40)
    for cls in classes:
        comment = cls.get("comment", "")
        print(f"  {cls['name']}: {comment}")


def list_properties(args):
    """列出所有属性"""
    manager = get_ontology_manager(args.dir)
    manager.load_all_modules()
    properties = manager.get_properties()

    print(f"\nProperties ({len(properties)}):")
    print("-" * 40)
    for prop in properties:
        comment = prop.get("comment", "")
        print(f"  {prop['name']} ({prop['type']}): {comment}")


def show_hierarchy(args):
    """显示类层次结构"""
    manager = get_ontology_manager(args.dir)
    manager.load_all_modules()
    hierarchy = manager.get_class_hierarchy()

    def print_hierarchy(tree, indent=0):
        for name, node in tree.items():
            print(f"{'  ' * indent}{name}")
            if node.get("children"):
                print_hierarchy(
                    {c["name"]: c for c in node["children"]},
                    indent + 1
                )

    print("\nClass Hierarchy:")
    print("-" * 40)
    print_hierarchy(hierarchy)


def validate_ontology(args):
    """验证本体"""
    manager = get_ontology_manager(args.dir)
    manager.load_all_modules()

    validator = get_ontology_validator(manager)
    result = validator.validate_all()

    print(f"\nValidation Result: {'PASS' if result.is_valid else 'FAIL'}")
    print(f"  Errors: {len(result.errors)}")
    print(f"  Warnings: {len(result.warnings)}")
    print(f"  Infos: {len(result.infos)}")

    if result.issues:
        print("\nIssues:")
        print("-" * 40)
        for issue in result.issues:
            print(f"  [{issue.severity.upper()}] {issue.message}")
            if issue.suggestion:
                print(f"    Suggestion: {issue.suggestion}")


def show_schema(args):
    """显示本体 Schema"""
    print(f"\nSchema: {STOCK_ONTOLOGY_SCHEMA.name}")
    print(f"Namespace: {STOCK_ONTOLOGY_SCHEMA.namespace}")
    print(f"\nClasses ({len(STOCK_ONTOLOGY_SCHEMA.classes)}):")
    for cls in STOCK_ONTOLOGY_SCHEMA.classes:
        print(f"  - {cls.name}: {cls.comment}")

    print(f"\nProperties ({len(STOCK_ONTOLOGY_SCHEMA.properties)}):")
    for prop in STOCK_ONTOLOGY_SCHEMA.properties[:10]:
        print(f"  - {prop.name} ({prop.property_type}): {prop.comment}")
    if len(STOCK_ONTOLOGY_SCHEMA.properties) > 10:
        print(f"  ... and {len(STOCK_ONTOLOGY_SCHEMA.properties) - 10} more")


def export_ontology(args):
    """导出本体"""
    manager = get_ontology_manager(args.dir)
    manager.load_all_modules()

    output_path = args.output or f"ontology_export.{args.format}"
    manager.save(output_path, args.format)
    print(f"Ontology exported to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Ontology Management Tool")
    parser.add_argument("--dir", default="ontology/core", help="Ontology directory")

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # load 命令
    subparsers.add_parser("load", help="Load ontology")

    # classes 命令
    subparsers.add_parser("classes", help="List all classes")

    # properties 命令
    subparsers.add_parser("properties", help="List all properties")

    # hierarchy 命令
    subparsers.add_parser("hierarchy", help="Show class hierarchy")

    # validate 命令
    subparsers.add_parser("validate", help="Validate ontology")

    # schema 命令
    subparsers.add_parser("schema", help="Show ontology schema")

    # export 命令
    export_parser = subparsers.add_parser("export", help="Export ontology")
    export_parser.add_argument("--output", "-o", help="Output file path")
    export_parser.add_argument(
        "--format", "-f",
        choices=["xml", "turtle", "n3", "nt"],
        default="xml",
        help="Output format"
    )

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return

    commands = {
        "load": load_ontology,
        "classes": list_classes,
        "properties": list_properties,
        "hierarchy": show_hierarchy,
        "validate": validate_ontology,
        "schema": show_schema,
        "export": export_ontology,
    }

    if args.command in commands:
        commands[args.command](args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
