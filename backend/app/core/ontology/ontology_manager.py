"""
本体管理器

提供本体的加载、保存、查询和管理功能。
使用 RDFLib 作为本体处理库。
"""

from typing import Any, Dict, List, Optional, Set, Tuple
from pathlib import Path
from loguru import logger

try:
    from rdflib import Graph, Namespace, RDF, RDFS, OWL, XSD, Literal, URIRef
    from rdflib.namespace import NamespaceManager
    RDFLIB_AVAILABLE = True
except ImportError:
    RDFLIB_AVAILABLE = False
    logger.warning("RDFLib not installed. Install with: pip install rdflib")

from app.config import settings


# 命名空间
STOCK_NS = Namespace("http://stock-ontology.org/")


class OntologyManager:
    """本体管理器"""

    def __init__(self, ontology_dir: str = None):
        """
        初始化本体管理器

        Args:
            ontology_dir: 本体文件目录
        """
        self.ontology_dir = Path(ontology_dir or settings.ONTOLOGY_DIR)
        self._graph: Optional[Any] = None
        self._loaded = False

        if not RDFLIB_AVAILABLE:
            logger.warning("RDFLib not available. Ontology features will be limited.")

    @property
    def graph(self):
        """获取 RDF 图"""
        if self._graph is None and RDFLIB_AVAILABLE:
            self._graph = Graph()
            self._graph.bind("stock", STOCK_NS)
            self._graph.bind("owl", OWL)
            self._graph.bind("rdfs", RDFS)
        return self._graph

    def load(self, file_path: str = None):
        """
        加载本体文件

        Args:
            file_path: 本体文件路径
        """
        if not RDFLIB_AVAILABLE:
            logger.error("RDFLib not available")
            return

        if file_path:
            load_path = Path(file_path)
        else:
            load_path = self.ontology_dir / "stock_ontology.owl"

        if load_path.exists():
            self.graph.parse(str(load_path), format="xml")
            self._loaded = True
            logger.info(f"Loaded ontology from {load_path}")
        else:
            logger.warning(f"Ontology file not found: {load_path}")

    def load_all_modules(self):
        """加载所有本体模块"""
        if not RDFLIB_AVAILABLE:
            logger.error("RDFLib not available")
            return

        module_files = [
            "company.owl",
            "industry.owl",
            "financial.owl",
            "event.owl",
            "investor.owl",
            "stock_ontology.owl",
        ]

        for module_file in module_files:
            file_path = self.ontology_dir / module_file
            if file_path.exists():
                try:
                    self.graph.parse(str(file_path), format="xml")
                    logger.info(f"Loaded module: {module_file}")
                except Exception as e:
                    logger.error(f"Failed to load {module_file}: {e}")

        self._loaded = True

    def save(self, file_path: str = None, format: str = "xml"):
        """
        保存本体

        Args:
            file_path: 保存路径
            format: 保存格式（xml/turtle/n3/nt）
        """
        if not RDFLIB_AVAILABLE:
            logger.error("RDFLib not available")
            return

        if file_path:
            save_path = Path(file_path)
        else:
            save_path = self.ontology_dir / "stock_ontology_export.owl"

        save_path.parent.mkdir(parents=True, exist_ok=True)
        self.graph.serialize(destination=str(save_path), format=format)
        logger.info(f"Saved ontology to {save_path}")

    def get_classes(self) -> List[Dict[str, Any]]:
        """
        获取所有类定义

        Returns:
            类定义列表
        """
        if not RDFLIB_AVAILABLE:
            return []

        classes = []
        for s in self.graph.subjects(RDF.type, OWL.Class):
            class_info = {
                "iri": str(s),
                "name": self._get_local_name(s),
                "comment": self._get_comment(s),
                "parents": [str(p) for p in self.graph.objects(s, RDFS.subClassOf)],
                "children": [str(c) for c in self.graph.subjects(RDFS.subClassOf, s)],
            }
            classes.append(class_info)

        return classes

    def get_class(self, class_name: str) -> Optional[Dict[str, Any]]:
        """
        获取指定类定义

        Args:
            class_name: 类名

        Returns:
            类定义字典
        """
        if not RDFLIB_AVAILABLE:
            return None

        class_uri = STOCK_NS[class_name]
        if (class_uri, RDF.type, OWL.Class) in self.graph:
            return {
                "iri": str(class_uri),
                "name": class_name,
                "comment": self._get_comment(class_uri),
                "parents": [str(p) for p in self.graph.objects(class_uri, RDFS.subClassOf)],
                "children": [str(c) for c in self.graph.subjects(RDFS.subClassOf, class_uri)],
            }
        return None

    def get_properties(self) -> List[Dict[str, Any]]:
        """
        获取所有属性定义

        Returns:
            属性定义列表
        """
        if not RDFLIB_AVAILABLE:
            return []

        properties = []

        # 对象属性
        for s in self.graph.subjects(RDF.type, OWL.ObjectProperty):
            prop_info = {
                "iri": str(s),
                "name": self._get_local_name(s),
                "type": "object",
                "comment": self._get_comment(s),
                "domain": [str(d) for d in self.graph.objects(s, RDFS.domain)],
                "range": [str(r) for r in self.graph.objects(s, RDFS.range)],
            }
            properties.append(prop_info)

        # 数据属性
        for s in self.graph.subjects(RDF.type, OWL.DatatypeProperty):
            prop_info = {
                "iri": str(s),
                "name": self._get_local_name(s),
                "type": "data",
                "comment": self._get_comment(s),
                "domain": [str(d) for d in self.graph.objects(s, RDFS.domain)],
                "range": [str(r) for r in self.graph.objects(s, RDFS.range)],
            }
            properties.append(prop_info)

        return properties

    def get_instances(self, class_name: str) -> List[Dict[str, Any]]:
        """
        获取指定类的所有实例

        Args:
            class_name: 类名

        Returns:
            实例列表
        """
        if not RDFLIB_AVAILABLE:
            return []

        class_uri = STOCK_NS[class_name]
        instances = []

        for s in self.graph.subjects(RDF.type, class_uri):
            instance_info = {
                "iri": str(s),
                "name": self._get_local_name(s),
                "class": class_name,
                "properties": self._get_resource_properties(s),
            }
            instances.append(instance_info)

        return instances

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取本体统计信息

        Returns:
            统计信息字典
        """
        if not RDFLIB_AVAILABLE:
            return {"error": "RDFLib not available"}

        classes = list(self.graph.subjects(RDF.type, OWL.Class))
        object_properties = list(self.graph.subjects(RDF.type, OWL.ObjectProperty))
        data_properties = list(self.graph.subjects(RDF.type, OWL.DatatypeProperty))

        return {
            "classes": len(classes),
            "object_properties": len(object_properties),
            "data_properties": len(data_properties),
            "triples": len(self.graph),
        }

    def get_class_hierarchy(self) -> Dict[str, Any]:
        """
        获取类层次结构

        Returns:
            类层次结构字典
        """
        if not RDFLIB_AVAILABLE:
            return {}

        hierarchy = {}

        def build_hierarchy(class_uri, depth=0):
            result = {
                "name": self._get_local_name(class_uri),
                "iri": str(class_uri),
                "depth": depth,
                "children": [],
            }
            for child in self.graph.subjects(RDFS.subClassOf, class_uri):
                result["children"].append(build_hierarchy(child, depth + 1))
            return result

        # 找到根类（没有父类的类）
        for class_uri in self.graph.subjects(RDF.type, OWL.Class):
            parents = list(self.graph.objects(class_uri, RDFS.subClassOf))
            if not parents or (len(parents) == 1 and str(parents[0]) == str(OWL.Thing)):
                name = self._get_local_name(class_uri)
                hierarchy[name] = build_hierarchy(class_uri)

        return hierarchy

    def query_sparql(self, query: str) -> List[Dict[str, Any]]:
        """
        执行 SPARQL 查询

        Args:
            query: SPARQL 查询语句

        Returns:
            查询结果
        """
        if not RDFLIB_AVAILABLE:
            return []

        try:
            results = self.graph.query(query)
            return [dict(row.asdict()) for row in results]
        except Exception as e:
            logger.error(f"SPARQL query failed: {e}")
            return []

    def validate(self) -> Dict[str, Any]:
        """
        验证本体

        Returns:
            验证结果
        """
        if not RDFLIB_AVAILABLE:
            return {"valid": False, "error": "RDFLib not available"}

        issues = []

        # 检查是否有类定义
        classes = list(self.graph.subjects(RDF.type, OWL.Class))
        if not classes:
            issues.append({
                "type": "error",
                "message": "No classes defined in ontology",
            })

        # 检查是否有属性定义
        properties = list(self.graph.subjects(RDF.type, OWL.ObjectProperty))
        properties += list(self.graph.subjects(RDF.type, OWL.DatatypeProperty))
        if not properties:
            issues.append({
                "type": "warning",
                "message": "No properties defined in ontology",
            })

        # 检查未定义域的属性
        for prop in properties:
            domains = list(self.graph.objects(prop, RDFS.domain))
            if not domains:
                issues.append({
                    "type": "warning",
                    "message": f"Property '{self._get_local_name(prop)}' has no domain",
                })

        return {
            "valid": len([i for i in issues if i["type"] == "error"]) == 0,
            "issues": issues,
        }

    def _get_local_name(self, uri) -> str:
        """获取 URI 的本地名称"""
        uri_str = str(uri)
        if "#" in uri_str:
            return uri_str.split("#")[-1]
        elif "/" in uri_str:
            return uri_str.split("/")[-1]
        return uri_str

    def _get_comment(self, uri) -> str:
        """获取资源的注释"""
        comments = list(self.graph.objects(uri, RDFS.comment))
        if comments:
            return str(comments[0])
        return ""

    def _get_resource_properties(self, uri) -> Dict[str, Any]:
        """获取资源的所有属性"""
        properties = {}
        for p, o in self.graph.predicate_objects(uri):
            if p != RDF.type:
                prop_name = self._get_local_name(p)
                if prop_name in properties:
                    if not isinstance(properties[prop_name], list):
                        properties[prop_name] = [properties[prop_name]]
                    properties[prop_name].append(str(o))
                else:
                    properties[prop_name] = str(o)
        return properties
