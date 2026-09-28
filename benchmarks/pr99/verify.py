"""Check the benchmark inputs and run the generator tests at both revisions."""

import ast
import io
import json
import subprocess
import sys
import types
import unittest
import warnings

import benchmark as bench


def read(revision: str, path: str) -> str:
    return subprocess.check_output(
        ["git", "show", f"{revision}:{path}"], cwd=bench.ROOT
    ).decode()


def method_body(revision: str, name: str) -> list[str]:
    tree = ast.parse(read(revision, bench.SOURCE))
    cls = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "Generator"
    )
    method = next(
        node
        for node in cls.body
        if isinstance(node, ast.FunctionDef) and node.name == name
    )
    body = method.body
    if isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
        body = body[1:]
    return [ast.dump(node) for node in body]


def main() -> None:
    assert method_body(bench.BASE, "next_id") == method_body(
        bench.HEAD, "_next_id_locked"
    )
    base, _ = bench.load_module(bench.BASE)
    head, _ = bench.load_module(bench.HEAD)
    for profile, (resolution, mids, bits, seqbits) in bench.PROFILES.items():
        sequences = []
        for module, cls in (
            (base, base.Generator),
            (base, base.ThreadSafeGenerator),
            (head, head.Generator),
        ):
            generator = cls(
                epoch=1700000000,
                resolution=getattr(module.Resolution, resolution),
                machine_ids=mids,
                machine_id_bits=bits,
                sequence_bits=seqbits,
            )
            generator.current_time = lambda: 1700001000.0
            values = [generator.next_id() for _ in range(10000)]
            assert len(set(values)) == len(values), profile
            sequences.append(values)
        assert sequences[0] == sequences[1] == sequences[2], profile
    assert head.ThreadSafeGenerator.next_id is head.Generator.next_id
    results = []
    for revision, generator_module in ((bench.BASE, base), (bench.HEAD, head)):
        package = types.ModuleType("jazzy_fish")
        package.__path__ = []
        sys.modules["jazzy_fish"] = package
        sys.modules["jazzy_fish.generator"] = generator_module
        suite = unittest.TestSuite()
        paths = ["python/tests/test_generator.py"]
        if revision == bench.HEAD:
            paths.append("python/tests/test_generator_concurrency.py")
        for path in paths:
            module = types.ModuleType("tests_" + path.rsplit("/", 1)[-1][:-3])
            exec(  # noqa: S102 - Execute tests from the inspected repository revision.
                compile(read(revision, path), f"{revision}/{path}", "exec"),
                module.__dict__,
            )
            suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(module))
        output = io.StringIO()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            result = unittest.TextTestRunner(stream=output, verbosity=2).run(suite)
        results.append(
            {
                "revision": revision,
                "tests": result.testsRun,
                "passed": result.wasSuccessful(),
                "output": output.getvalue(),
            }
        )
    print(
        json.dumps(
            {
                "runtime": bench.runtime_metadata(),
                "core_ast_equal": True,
                "deterministic_profiles": len(bench.PROFILES),
                "tests": results,
            }
        )
    )
    if any(not result["passed"] for result in results):
        sys.exit(1)


if __name__ == "__main__":
    main()
