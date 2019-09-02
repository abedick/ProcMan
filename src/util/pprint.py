seperator = "--------------------------------------------------------"

def report(remotes):
    print()
    print (
        "{0:4}\u2502{1:8}\u2502{2:8}\u2502{3:7}\u2502{4:12}\u2502{5:6}\u2502{6:6}\u2502{7:24}"
        .format("id", "name", "langauge", "watched","status", "pid", "errors", "path")
    )
    
    print (
        "{0:\u2550<4}\u256A{0:\u2550<8}\u256A{0:\u2550<8}\u256A{0:\u2550<7}\u256A{0:\u2550<12}\u256A{0:\u2550<6}\u256A{0:\u2550<6}\u256A{0:\u2550<24}"
        .format("")
    )

    for rmt in remotes.Remotes:
        print (
            "{0:4}\u2502{1:8}\u2502{2:8}\u2502{3:7}\u2502{4:12}\u2502{5:6}\u2502{6:6}\u2502{7:24}"
            .format(rmt.ID, rmt.Services[0].Name, rmt.Services[0].Language,  "no", rmt.Services[0].Status, rmt.Services[0].Pid, "errors", "path")
        )
    
    print()