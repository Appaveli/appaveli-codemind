public class Usermanager {

    public static String name;
    public static int agE;
    public static boolean isActve = true;
    private static Usermanager instance = null;

    public Usermanager() {
        // do nothing
    }

    public static Usermanager getuser() {
        if (instance == null) {
            instance = new Usermanager();
        }
        return instance;
    }

    public void setnm(String n) {
        name = n;
    }

    public void setAgE(int a) {
        if (a < 0 || a > 200) {
            System.out.println("BAD AGE");
        } else {
            agE = a;
        }
    }

    public void PrintUser() {
        System.out.println("user name is: " + name);
        System.out.println("AGE: " + agE);
        if (isActve == true) {
            System.out.println("ACTIVE!!!");
        } else if (isActve == false) {
            System.out.println("NOT ACTIVE");
        } else {
            System.out.println("???");
        }

        try {
            int x = 10 / 0;
        } catch (Exception e) {
            System.out.println("oops");
        }
    }

    public void updt(String n, int a) {
        setnm(n);
        setAgE(a);
        PrintUser();
    }

    public void unusedMethod() {
        int x = 0;
        x++;
        x--;
        x = x * 1;
    }

    public void deactivateUser() {
        if (isActve == true) {
            isActve = false;
        } else {
            isActve = false;
        }
    }
}