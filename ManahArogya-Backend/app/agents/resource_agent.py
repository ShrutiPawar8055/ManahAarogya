class ResourceAgent:
    """Simple rule-based resource recommendation helper."""

    def recommend_categories(self, severity_labels: list[str]) -> list[str]:
        """Map assessment severity labels to resource categories."""
        categories: list[str] = []
        if any(label in {"moderate", "severe", "moderately severe"} for label in severity_labels):
            categories.append("counseling")
        if any(label in {"mild", "moderate", "severe", "moderately severe"} for label in severity_labels):
            categories.append("anxiety")
        if "minimal" in severity_labels or not categories:
            categories.append("sleep")
        return list(dict.fromkeys(categories))


resource_agent = ResourceAgent()
