"""
Integration and End-to-End Tests for Optional $ Syntax.

Tests complete programs using mixed assignment syntax to ensure
all components work together correctly.
"""

import json

import pytest

from cy_language import Cy


class TestOptionalDollarIntegration:
    """Test complete integration scenarios for optional $ syntax."""

    def setup_method(self):
        """Set up test fixtures."""
        # Load all native functions for complete testing
        import cy_language.native_functions  # noqa: F401
        from cy_language.ui.tools import default_registry

        self.cy = Cy(tools=default_registry.get_tools_dict())

    def test_complete_program_mixed_syntax(self):
        """Test complete program mixing $var and var assignment."""
        program = """# User data processing with mixed syntax
user_name = "Alice Smith"
user_age = 25
user_email = "alice@example.com"
is_premium = True

# Process user data
if (user_age >= 18 and is_premium) {
    account_type = "Premium Adult"
    discount = 0.15
} else {
    account_type = "Standard"
    discount = 0.0
}

# Calculate some metrics
name_length = len(user_name)
email_length = len(user_email)

# Generate output
result = {
    "user": {
        "name": user_name,
        "age": user_age,
        "email": user_email,
        "account_type": account_type
    },
    "metrics": {
        "name_length": name_length,
        "email_length": email_length,
        "discount": discount
    }
}
output = result
return output"""

        result = self.cy.run(program)

        # Parse result directly (JSON output)
        data = json.loads(result)

        assert data["user"]["name"] == "Alice Smith"
        assert data["user"]["age"] == 25
        assert data["user"]["email"] == "alice@example.com"
        assert data["user"]["account_type"] == "Premium Adult"
        assert data["metrics"]["name_length"] == 11  # len("Alice Smith")
        assert data["metrics"]["email_length"] == 17  # len("alice@example.com")
        assert data["metrics"]["discount"] == 0.15

    def test_complex_data_processing_pipeline(self):
        """Test complex data processing with mixed variable syntax."""
        program = """# Data processing pipeline
raw_data = [
    {"name": "Alice", "scores": [85, 90, 95]},
    {"name": "Bob", "scores": [70, 75, 80]},
    {"name": "Charlie", "scores": [95, 100, 90]}
]

processed_users = []
index = 0
while (index < 3) {
    current_user = raw_data[index]
    user_name = current_user["name"]
    user_scores = current_user["scores"]
    
    # Calculate average (simplified)
    total = user_scores[0] + user_scores[1] + user_scores[2]
    average = total / 3
    
    # Determine grade
    if (average >= 90) {
        grade = "A"
    } elif (average >= 80) {
        grade = "B"
    } else {
        grade = "C"
    }
    
    # Create user summary (simplified - would normally append to list)
    if (index == 2) {  # Just capture last user for output
        final_user = {
            "name": user_name,
            "average": average,
            "grade": grade,
            "score_count": len(user_scores)
        }
    }
    
    index = index + 1
}

output = final_user
return output"""

        result = self.cy.run(program)

        # Parse result directly (JSON output)
        data = json.loads(result)

        assert data["name"] == "Charlie"
        assert data["average"] == 95.0  # (95+100+90)/3
        assert data["grade"] == "A"
        assert data["score_count"] == 3

    def test_string_interpolation_comprehensive(self):
        """Test comprehensive string interpolation with mixed assignments."""
        program = '''# Mixed variable assignments
first_name = "Alice"
last_name = "Johnson"
age = 25
title = "Dr."
department = "Engineering"
company = "TechCorp"

# Create comprehensive report using interpolation
report = """
Employee Information Report
===========================

Personal Details:
- Full Name: ${title} ${first_name} ${last_name}
- Age: ${age} years old
- Department: ${department}
- Company: ${company}

Summary:
${title} ${last_name} is a ${age}-year-old professional 
working in ${department} at ${company}.

Contact: ${first_name}.${last_name}@techcorp.com
"""

output = report
return output'''

        result = self.cy.run(program)

        # Verify interpolation worked correctly
        assert "Dr. Alice Johnson" in result
        assert "25 years old" in result
        assert "Engineering" in result
        assert "TechCorp" in result
        assert "Alice.Johnson@techcorp.com" in result

    def test_error_handling_scenarios(self):
        """Test error scenarios with mixed syntax."""
        # Test undefined variable access
        program = """name = "Alice"
output = "Hello ${undefined_var}!"
return output"""

        with pytest.raises(Exception):  # Should raise variable not found
            self.cy.run(program)

    def test_backward_compatibility_comprehensive(self):
        """Test comprehensive backward compatibility."""
        # This program uses only traditional $var syntax
        program = """name = "Alice"
age = 25
scores = [85, 90, 95]
total = scores[0] + scores[1] + scores[2]
average = total / 3

if (average >= 90) {
    grade = "A"
} else {
    grade = "B"
}

output = "Student: ${name}, Age: ${age}, Grade: ${grade}"
return output"""

        result = self.cy.run(program)
        assert result == '"Student: Alice, Age: 25, Grade: A"'

    def test_performance_with_many_variables(self):
        """Test performance doesn't degrade with many mixed variables."""
        program = """# Create many variables with mixed syntax
var1 = "value1"
var2 = "value2"
var3 = "value3"
var4 = "value4"
var5 = "value5"
var6 = "value6"
var7 = "value7"
var8 = "value8"
var9 = "value9"
var10 = "value10"

# Use them all in an expression
result = var1 + var2 + var3 + var4 + var5 + var6 + var7 + var8 + var9 + var10
output = len(result)
return output"""

        result = self.cy.run(program)
        assert (
            result == "61"
        )  # 9 * 6 chars ("value" + single digit) + 7 chars ("value10")

    def test_nested_data_structures_mixed_syntax(self):
        """Test nested data structures with mixed variable syntax."""
        program = """# Build nested structure with mixed syntax
company_name = "TechCorp"
departments = {}

# Engineering department
eng_dept = {
    "name": "Engineering",
    "head": "Alice Smith",
    "budget": 500000
}
departments["engineering"] = eng_dept

# Sales department  
sales_dept = {
    "name": "Sales", 
    "head": "Bob Johnson",
    "budget": 300000
}
departments["sales"] = sales_dept

# Generate report
eng_head = departments["engineering"]["head"]
sales_budget = departments["sales"]["budget"]

report = {
    "company": company_name,
    "eng_head": eng_head,
    "sales_budget": sales_budget,
    "total_depts": len(departments)
}

output = report
return output"""

        result = self.cy.run(program)

        # Parse and verify (JSON output)
        data = json.loads(result)
        assert data["company"] == "TechCorp"
        assert data["eng_head"] == "Alice Smith"
        assert data["sales_budget"] == 300000
        assert data["total_depts"] == 2

    def test_function_calls_with_mixed_variables(self):
        """Test function calls using variables assigned with mixed syntax."""
        program = """text1 = "Hello"
text2 = "World"
text3 = "from Cy Language"

# Use len function with mixed variable forms
len1 = len(text1)
len2 = len(text2)
len3 = len(text3)

total_length = len1 + len2 + len3

output = {
    "text1_len": len1,
    "text2_len": len2,
    "text3_len": len3,
    "total": total_length
}
return output"""

        result = self.cy.run(program)

        # Parse and verify (JSON output)
        data = json.loads(result)
        assert data["text1_len"] == 5  # "Hello"
        assert data["text2_len"] == 5  # "World"
        assert data["text3_len"] == 16  # "from Cy Language"
        assert data["total"] == 26

    def test_real_world_config_processing(self):
        """Test real-world-like configuration processing."""
        program = """# Configuration processing scenario
config_raw = {
    "database": {
        "host": "localhost",
        "port": 5432,
        "name": "app_db"
    },
    "redis": {
        "host": "redis.example.com", 
        "port": 6379
    },
    "app": {
        "debug": False,
        "max_connections": 100
    }
}

# Extract and process configuration
db_host = config_raw["database"]["host"]
db_port = config_raw["database"]["port"]
redis_host = config_raw["redis"]["host"]
app_debug = config_raw["app"]["debug"]
max_conn = config_raw["app"]["max_connections"]

# Build connection strings
db_connection = "postgresql://${db_host}:${db_port}/app_db"
redis_connection = "redis://${redis_host}:6379"

# Final configuration
final_config = {
    "db_conn": db_connection,
    "redis_conn": redis_connection,
    "debug_mode": app_debug,
    "max_connections": max_conn,
    "connection_string_length": len(db_connection)
}

output = final_config
return output"""

        result = self.cy.run(program)

        # Parse and verify
        data = json.loads(result)
        assert data["db_conn"] == "postgresql://localhost:5432/app_db"
        assert data["redis_conn"] == "redis://redis.example.com:6379"
        assert data["debug_mode"] is False
        assert data["max_connections"] == 100
        assert data["connection_string_length"] == 34
