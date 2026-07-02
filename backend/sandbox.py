import subprocess
import os
from typing import Dict, Any, List

# Establish clean absolute paths relative to this script's location
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(BACKEND_DIR, ".."))
RUNNER_DIR = os.path.join(ROOT_DIR, "runner")

def run_dryrun(code_string: str, data_type: str, array_state: str, range_start: int, range_end: int, must_have: str):
    # 1. Dynamically overwrite runner/Sorter.java based on the data type
    sorter_path = os.path.join(RUNNER_DIR, "Sorter.java")
    java_type = "double" if data_type == "decimal" else "int"
    sorter_code = f"package runner;\n\npublic interface Sorter {{\n    void sort({java_type}[] arr);\n}}\n"
    with open(sorter_path, "w", encoding="utf-8") as f:
        f.write(sorter_code)

    # 1.5 Dynamically write DryRunDriver.java
    driver_path = os.path.join(RUNNER_DIR, "DryRunDriver.java")
    
    java_array_type = "double[]" if data_type == "decimal" else "int[]"
    rand_call = f"{range_start} + ({range_end} - {range_start}) * rand.nextDouble()" if data_type == "decimal" else f"rand.nextInt(Math.max(1, {range_end} - {range_start})) + {range_start}"
    
    parsed_must_have = ""
    if must_have and must_have.strip():
        parts = [p.strip() for p in must_have.split(',') if p.strip()]
        if data_type == "decimal":
            valid_parts = [p for p in parts if p.replace('.','',1).replace('-','',1).isdigit()]
        else:
            valid_parts = [p for p in parts if p.replace('-','',1).isdigit()]
        parsed_must_have = ", ".join(valid_parts)
    
    driver_code = f"""package runner;
import java.util.Random;
import java.util.Arrays;

public class DryRunDriver {{
    public static void main(String[] args) {{
        Sorter sorter = new UserSolution();
        Random rand = new Random(42);
        
        // 1. Functional output check on N=15
        {java_array_type} arr15 = new {java_array_type.replace('[]', '[15]')};
        for(int i=0; i<15; i++) arr15[i] = {rand_call};
        
        {java_array_type} mustHave = new {java_array_type.replace('[]', '[]')} {{{parsed_must_have}}};
        for(int i = 0; i < mustHave.length && i < 15; i++) {{
            int pos = rand.nextInt(15);
            arr15[pos] = mustHave[i];
        }}
        
        System.out.println("INPUT : " + Arrays.toString(arr15));
        
        // Warmup JIT slightly to stabilize initial timer
        for(int i=0; i<100; i++) {{
            {java_array_type} warmup = new {java_array_type.replace('[]', '[10]')};
            for(int j=0; j<10; j++) warmup[j] = {rand_call};
            sorter.sort(warmup);
        }}
        
        sorter.sort(arr15);
        System.out.println("OUTPUT: " + Arrays.toString(arr15));
        
        // 2. Exponential Growth Check (15 vs 25)
        long[] times = new long[3];
        int[] sizes = {{15, 20, 25}};
        for (int i = 0; i < 3; i++) {{
            {java_array_type} testArr = new {java_array_type.replace('[]', '')}[sizes[i]];
            for(int j=0; j<sizes[i]; j++) testArr[j] = {rand_call};
            
            long start = System.nanoTime();
            sorter.sort(testArr);
            times[i] = System.nanoTime() - start;
        }}
        
        long t15 = Math.max(1, times[0]);
        long t25 = Math.max(1, times[2]);
        double growth = (double) t25 / t15;
        
        // Cubic O(N^3) growth from 15 to 25 is (25/15)^3 = 4.6x
        // If growth > 10.0x, it is definitively super-polynomial (exponential)
        if (growth > 10.0) {{
            System.err.println("\\n[!] Exponential Complexity Detected! Growth ratio " + String.format("%.1fx", growth) + " vastly exceeds polynomial limits.");
            System.exit(1);
        }}
    }}
}}"""
    with open(driver_path, "w", encoding="utf-8") as f:
        f.write(driver_code)

    # 2. Overwrite runner/UserSolution.java
    user_solution_path = os.path.join(RUNNER_DIR, "UserSolution.java")
    with open(user_solution_path, "w", encoding="utf-8") as f:
        f.write(code_string)

    # 3. Compile
    compile_res = subprocess.run(
        ["javac", "runner/DryRunDriver.java", "runner/Sorter.java", "runner/UserSolution.java"],
        cwd=ROOT_DIR,
        capture_output=True, text=True
    )
    if compile_res.returncode != 0:
        raise Exception("Compilation error: " + compile_res.stderr.strip())

    # 4. Execute DryRunDriver
    run_res = subprocess.run(
        ["java", "runner.DryRunDriver", data_type],
        cwd=ROOT_DIR,
        capture_output=True, text=True, timeout=2
    )
    
    output = run_res.stdout.strip()
    if run_res.stderr:
        output += "\n" + run_res.stderr.strip()
        
    return "See output below", output

def run_sandbox(code_string: str, data_type: str, array_state: str, range_start: int, range_end: int, must_have: str):
    """
    Natively writes, compiles, and benchmarks user-submitted Java sorting code,
    capturing performance data directly from the OS process streams.
    """
    # 1. Dynamically overwrite runner/Sorter.java based on the data type
    sorter_path = os.path.join(RUNNER_DIR, "Sorter.java")
    java_type = "double" if data_type == "decimal" else "int"
    sorter_code = f"package runner;\n\npublic interface Sorter {{\n    void sort({java_type}[] arr);\n}}\n"
    with open(sorter_path, "w", encoding="utf-8") as f:
        f.write(sorter_code)

    # 1.5 Dynamically generate runner/BenchmarkDriver.java from the template
    template_path = os.path.join(RUNNER_DIR, "BenchmarkDriver.template.txt")
    driver_path = os.path.join(RUNNER_DIR, "BenchmarkDriver.java")
    
    with open(template_path, "r", encoding="utf-8") as f:
        template_code = f.read()
        
    template_code = template_code.replace("TYPE_ARRAY_INIT", java_type)
    template_code = template_code.replace("TYPE_ARRAY", java_type + "[]")
    template_code = template_code.replace("TYPE_VAR", java_type)
    
    if data_type == "decimal":
        template_code = template_code.replace("TYPE_RANDOM_CALL", "start + (end - start) * rand.nextDouble()")
        sorted_gen = """double currentVal = start;
            double step = (double)(end - start) / size;
            for (int i = 0; i < size; i++) {
                arr[i] = currentVal + (rand.nextDouble() * step);
                currentVal += step;
            }"""
        template_code = template_code.replace("TYPE_SORTED_GEN", sorted_gen)
    else:
        template_code = template_code.replace("TYPE_RANDOM_CALL", "rand.nextInt(bound) + start")
        sorted_gen = """int currentVal = start;
            for (int i = 0; i < size; i++) {
                arr[i] = currentVal;
                if (size - i > 0 && rand.nextDouble() < (double)(end - currentVal) / (size - i)) {
                    currentVal++;
                }
            }"""
        template_code = template_code.replace("TYPE_SORTED_GEN", sorted_gen)

    parsed_must_have = ""
    if must_have and must_have.strip():
        parts = [p.strip() for p in must_have.split(',') if p.strip()]
        if data_type == "decimal":
            valid_parts = [p for p in parts if p.replace('.','',1).replace('-','',1).isdigit()]
        else:
            valid_parts = [p for p in parts if p.replace('-','',1).isdigit()]
        parsed_must_have = ", ".join(valid_parts)
    template_code = template_code.replace("MUST_HAVE_VALUES", parsed_must_have)

    with open(driver_path, "w", encoding="utf-8") as f:
        f.write(template_code)

    # 2. Overwrite runner/UserSolution.java with the fresh user submission
    user_solution_path = os.path.join(RUNNER_DIR, "UserSolution.java")
    with open(user_solution_path, "w", encoding="utf-8") as f:
        f.write(code_string)

    try:
        # 3. Programmatically compile the Java directory
        compile_res = subprocess.run(
            ["javac", "runner/*.java"],
            cwd=ROOT_DIR,
            capture_output=True,
            text=True,
            shell=True
        )

        if compile_res.returncode != 0:
            raise Exception("Compilation error: " + compile_res.stderr.strip())

        # 4. Execute the BenchmarkDriver with configuration arguments
        run_res = subprocess.run(
            ["java", "runner.BenchmarkDriver", data_type, array_state, str(range_start), str(range_end)],
            cwd=ROOT_DIR,
            capture_output=True,
            text=True,
            timeout=60  # Increased to 60 seconds for O(N^3) nested loops
        )

        # Catch active runtime exceptions or verification logic assertions
        if run_res.returncode != 0:
            raise Exception("Runtime error: " + run_res.stderr.strip())

    except subprocess.TimeoutExpired:
        raise Exception("Execution Limit Exceeded! Your algorithm exceeded the maximum allotted runtime threshold.")