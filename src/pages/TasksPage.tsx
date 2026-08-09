import {
  useEffect,
  useState,
} from "react";

import {
  getTasks,
  completeTask,
} from "../api";

import type {
  TaskItem,
} from "../types";

import {
  haptic,
} from "../telegram";


type TaskPeriod =
  | "all"
  | "daily"
  | "weekly"
  | "monthly"
  | "permanent";


export default function TasksPage() {

  const [
    tasks,
    setTasks,
  ] = useState<TaskItem[]>([]);

  const [
    period,
    setPeriod,
  ] = useState<TaskPeriod>(
    "all"
  );

  const [
    loading,
    setLoading,
  ] = useState(true);

  const [
    completing,
    setCompleting,
  ] = useState<number | null>(
    null
  );

  const [
    error,
    setError,
  ] = useState<string | null>(
    null
  );


  useEffect(() => {
    loadTasks();
  }, []);


  async function loadTasks() {

    setLoading(true);
    setError(null);

    try {

      const data =
        await getTasks();

      setTasks(data);

    } catch {

      setError(
        "Не удалось загрузить задания."
      );

    } finally {

      setLoading(false);

    }
  }


  async function handleComplete(
    task: TaskItem
  ) {

    if (
      completing !== null
    ) {
      return;
    }

    if (
      task.completed
    ) {
      return;
    }

    haptic("light");

    setCompleting(
      task.id
    );

    try {

      const result =
        await completeTask(
          task.id
        );

      if (
        result.success
      ) {

        setTasks(
          previous =>
            previous.map(
              item =>
                item.id ===
                task.id
                  ? {
                      ...item,
                      completed:
                        true,
                    }
                  : item
            )
        );

        haptic(
          "success"
        );

      }

    } catch {

      setError(
        "Не удалось выполнить задание."
      );

    } finally {

      setCompleting(
        null
      );

    }
  }


  const visibleTasks =
    tasks.filter(
      task =>
        period === "all"
          ? true
          : task.period ===
            period
    );


  return (
    <div className="page tasks-page">

      <div className="section-title">
        📋 Задания
      </div>

      <div className="section-subtitle">
        Выполняй задания и получай
        награды.
      </div>


      <div className="tasks-periods">

        <button
          className={
            period === "all"
              ? "task-period active"
              : "task-period"
          }
          onClick={() =>
            setPeriod("all")
          }
        >
          Все
        </button>

        <button
          className={
            period === "daily"
              ? "task-period active"
              : "task-period"
          }
          onClick={() =>
            setPeriod("daily")
          }
        >
          📅 Ежедневные
        </button>

        <button
          className={
            period === "weekly"
              ? "task-period active"
              : "task-period"
          }
          onClick={() =>
            setPeriod("weekly")
          }
        >
          📆 Недельные
        </button>

        <button
          className={
            period === "monthly"
              ? "task-period active"
              : "task-period"
          }
          onClick={() =>
            setPeriod("monthly")
          }
        >
          🗓 Месячные
        </button>

      </div>


      {loading && (

        <div className="empty-state">

          <div className="loader-spinner" />

          <p>
            Загружаем задания...
          </p>

        </div>

      )}


      {!loading &&
        error && (

          <div className="empty-state">

            <div className="empty-icon">
              ⚠️
            </div>

            <strong>
              Ошибка
            </strong>

            <p>
              {error}
            </p>

            <button
              className="primary-button"
              onClick={
                loadTasks
              }
            >
              Повторить
            </button>

          </div>

        )}


      {!loading &&
        !error &&
        visibleTasks.length ===
          0 && (

          <div className="empty-state">

            <div className="empty-icon">
              📋
            </div>

            <strong>
              Заданий пока нет
            </strong>

            <p>
              Новые задания появятся
              здесь позже.
            </p>

          </div>

        )}


      {!loading &&
        !error &&
        visibleTasks.length >
          0 && (

          <div className="tasks-list">

            {visibleTasks.map(
              task => (

                <article
                  className={
                    task.completed
                      ? "task-card completed"
                      : "task-card"
                  }
                  key={task.id}
                >

                  <div className="task-card-top">

                    <div className="task-icon">

                      {task.only_premium
                        ? "💎"
                        : "📋"}

                    </div>

                    <div className="task-info">

                      <div className="task-title">

                        {task.title}

                      </div>

                      {task.description && (

                        <div className="task-description">

                          {
                            task.description
                          }

                        </div>

                      )}

                    </div>

                  </div>


                  <div className="task-reward">

                    <span>
                      🎁
                    </span>

                    <span>
                      {formatReward(
                        task
                      )}
                    </span>

                  </div>


                  <div className="task-footer">

                    <span className="task-period-label">

                      {getPeriodLabel(
                        task.period
                      )}

                    </span>


                    {task.completed ? (

                      <button
                        className="task-completed-button"
                        disabled
                      >
                        ✅ Выполнено
                      </button>

                    ) : (

                      <button
                        className="task-complete-button"
                        disabled={
                          completing ===
                          task.id
                        }
                        onClick={() =>
                          handleComplete(
                            task
                          )
                        }
                      >

                        {completing ===
                        task.id
                          ? "Проверяем..."
                          : "Выполнить"}

                      </button>

                    )}

                  </div>

                </article>

              )
            )}

          </div>

        )}

    </div>
  );
}


// =========================================================
// REWARD
// =========================================================

function formatReward(
  task: TaskItem
): string {

  if (
    task.reward_type ===
      "stars" ||
    task.reward_type ===
      "star"
  ) {

    return (
      `+${task.reward_amount} Stars`
    );

  }


  if (
    task.reward_type ===
      "balance" ||
    task.reward_type ===
      "rub"
  ) {

    return (
      `+${task.reward_amount.toLocaleString(
        "ru-RU"
      )} ₽`
    );

  }


  if (
    task.reward_type ===
      "search" ||
    task.reward_type ===
      "searches"
  ) {

    return (
      `+${task.reward_amount} поисков`
    );

  }


  if (
    task.reward_type ===
      "trap" ||
    task.reward_type ===
      "traps"
  ) {

    return (
      `+${task.reward_amount} ловушек`
    );

  }


  if (
    task.reward_type ===
      "discount" ||
    task.reward_type ===
      "discount_percent"
  ) {

    return (
      `-${task.reward_amount}%`
    );

  }


  if (
    task.reward_type ===
      "premium" ||
    task.reward_type ===
      "premium_days"
  ) {

    const days =
      task.premium_days ||
      task.reward_amount;

    return (
      `Premium на ${days} дн.`
    );

  }


  return (
    `+${task.reward_amount}`
  );
}


// =========================================================
// PERIOD
// =========================================================

function getPeriodLabel(
  period: string
): string {

  switch (
    period
  ) {

    case "daily":
      return "📅 Ежедневное";

    case "weekly":
      return "📆 Недельное";

    case "monthly":
      return "🗓 Месячное";

    case "permanent":
      return "♾ Постоянное";

    default:
      return "📋 Задание";
  }
}
