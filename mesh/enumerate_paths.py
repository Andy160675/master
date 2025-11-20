from itertools import permutations
from mesh.topology import Topology
from mesh.router import validate_path


def enumerate_valid_triples():
    topo = Topology()
    pods = topo.all_pods()
    valid = []
    for a, b, c in permutations(pods, 3):
        path = [a, b, c]
        check = validate_path(topo, path, critical=True)
        if check.valid:
            valid.append(path)
    return valid


if __name__ == "__main__":
    paths = enumerate_valid_triples()
    print(f"Found {len(paths)} valid 3-pod paths:\n")
    for p in paths:
        print(" -> ".join(p))
