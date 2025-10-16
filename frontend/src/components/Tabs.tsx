import {
  HTMLAttributes,
  ReactElement,
  ReactNode,
  cloneElement,
  createContext,
  isValidElement,
  useContext,
} from "react";

interface TabsContextValue {
  value: string;
  onValueChange?: (value: string) => void;
}

const TabsContext = createContext<TabsContextValue | null>(null);

function useTabsContext(): TabsContextValue {
  const context = useContext(TabsContext);
  if (!context) {
    throw new Error("Tabs components must be used within <Tabs.Root>");
  }
  return context;
}

interface RootProps extends HTMLAttributes<HTMLDivElement> {
  value: string;
  onValueChange?: (value: string) => void;
  children: ReactNode;
}

export function Root({ value, onValueChange, children, ...props }: RootProps) {
  return (
    <TabsContext.Provider value={{ value, onValueChange }}>
      <div {...props}>{children}</div>
    </TabsContext.Provider>
  );
}

export function List({ children, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div role="tablist" {...props}>
      {children}
    </div>
  );
}

function composeEventHandlers<E = any>(
  originalHandler: ((event: E) => void) | undefined,
  ourHandler: ((event: E) => void) | undefined
) {
  return (event: E) => {
    originalHandler?.(event);
    if (!(event as any)?.defaultPrevented) {
      ourHandler?.(event);
    }
  };
}

interface TriggerProps extends HTMLAttributes<HTMLButtonElement> {
  value: string;
  asChild?: boolean;
  children: ReactNode;
}

export function Trigger({ value, asChild = false, children, ...props }: TriggerProps) {
  const { value: activeValue, onValueChange } = useTabsContext();
  const isActive = activeValue === value;
  const handleClick = () => onValueChange?.(value);

  if (asChild && isValidElement(children)) {
    const child = children as ReactElement;
    return cloneElement(child, {
      role: "tab",
      "data-state": isActive ? "active" : "inactive",
      "aria-selected": isActive,
      onClick: composeEventHandlers(child.props.onClick, (event: any) => {
        handleClick();
        props.onClick?.(event);
      }),
    });
  }

  return (
    <button
      type="button"
      role="tab"
      aria-selected={isActive}
      data-state={isActive ? "active" : "inactive"}
      onClick={composeEventHandlers(props.onClick, () => handleClick())}
      {...props}
    >
      {children}
    </button>
  );
}

interface ContentProps extends HTMLAttributes<HTMLDivElement> {
  value: string;
  children: ReactNode;
}

export function Content({ value, children, ...props }: ContentProps) {
  const { value: activeValue } = useTabsContext();
  if (activeValue !== value) {
    return null;
  }
  return (
    <div role="tabpanel" data-state="active" {...props}>
      {children}
    </div>
  );
}

